"""Execução completa da matriz topologia x carga x algoritmo x repetições.

Uso: python3.11 -m experiments.run_all --config experiments/configs/default.json

A execução é sequencial de propósito: o tempo de decisão é métrica do TCC e
paralelismo distorceria as medições. A unidade de gravação (e de retomada) é a
célula (topologia, nível de carga), que roda todos os algoritmos juntos para
manter a rotação de ordem entre repetições feita pelo ExperimentRunner.
"""

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

from experiments.cli import ALGORITHMS, TOPOLOGIES, create_algorithm_specs, executar_celula
from experiments.scenarios import LoadLevel, ScenarioConfig, load_config
from metrics.exporter import MetricsExporter

MARCADOR = "celula.json"
ARQUIVOS_CELULA = ("runs.json", "runs.csv", "aggregates.csv")


@dataclass(frozen=True)
class Celula:
    topology: str
    level: LoadLevel
    repetitions: int

    @property
    def rotulo(self) -> str:
        return f"{self.topology}/{self.level.name}"

    @property
    def peso(self) -> int:
        """Custo relativo aproximado, usado só para a ETA."""
        return self.repetitions * self.level.requests


def planejar(config: ScenarioConfig, topologies, repetitions) -> list[Celula]:
    return [
        Celula(topology, level, repetitions)
        for topology in topologies for level in config.load_levels
    ]


def planejar_estimativa(config: ScenarioConfig, topologies) -> list[Celula]:
    """Versão reduzida: as 2 topologias menores completas (2 rep.), as demais
    só no primeiro e no último nível (1 rep.)."""
    por_tamanho = sorted(
        topologies, key=lambda nome: len(TOPOLOGIES[nome]().nodes)
    )
    menores = set(por_tamanho[:2])
    celulas = []
    for topology in topologies:
        if topology in menores:
            niveis, reps = config.load_levels, 2
        else:
            niveis, reps = (config.load_levels[0], config.load_levels[-1]), 1
        celulas.extend(Celula(topology, level, reps) for level in niveis)
    return celulas


def _assinatura(config, celula, specs, seed) -> dict:
    return {
        "topology": celula.topology,
        "load_level": celula.level.name,
        "requests": celula.level.requests,
        "multiplier": celula.level.multiplier,
        "repetitions": celula.repetitions,
        "seed": seed,
        "algorithms": [spec.name for spec in specs],
        "parameters": {spec.name: spec.parameters for spec in specs},
        "link_capacity": config.link_capacity,
        "base_bandwidth": config.base_bandwidth,
        "noise": config.noise,
        "profile": config.profile.factors,
    }


def celula_concluida(raiz: Path, celula: Celula, assinatura: dict) -> bool:
    """True se a célula está gravada por completo e com a mesma assinatura."""
    pasta = raiz / celula.topology / celula.level.name
    marcador = pasta / MARCADOR
    if not marcador.is_file() or any(not (pasta / n).is_file() for n in ARQUIVOS_CELULA):
        return False
    try:
        salvo = json.loads(marcador.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return salvo.get("assinatura") == json.loads(json.dumps(assinatura))


def gravar_celula(raiz: Path, celula: Celula, runs, aggregates, extra: dict) -> Path:
    """Grava a célula numa pasta temporária e a renomeia (troca atômica)."""
    destino = raiz / celula.topology / celula.level.name
    temporaria = raiz / f".tmp-{celula.topology}-{celula.level.name}"
    if temporaria.exists():
        shutil.rmtree(temporaria)
    exporter = MetricsExporter()
    exporter.export_json(runs, temporaria / "runs.json", aggregates=aggregates)
    exporter.export_csv(runs, temporaria / "runs.csv")
    exporter.export_aggregates_csv(aggregates, temporaria / "aggregates.csv")
    (temporaria / MARCADOR).write_text(
        json.dumps(extra, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if destino.exists():
        shutil.rmtree(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    os.replace(temporaria, destino)
    return destino


def tempos_de_alocacao(runs) -> dict[str, float]:
    """Soma, por algoritmo, dos tempos de allocate (todas as repetições)."""
    tempos: dict[str, float] = {}
    for run in runs:
        nome = run.metadata.algorithm
        tempos[nome] = tempos.get(nome, 0.0) + run.summary.timing.total_seconds
    return tempos


def consolidar(raiz: Path, celulas: list[Celula]) -> list[Path]:
    """Junta os CSV das células em todas_execucoes.csv e todos_agregados.csv."""
    gerados = []
    for origem, destino in (
        ("runs.csv", "todas_execucoes.csv"),
        ("aggregates.csv", "todos_agregados.csv"),
    ):
        linhas, campos = [], []
        for celula in celulas:
            arquivo = raiz / celula.topology / celula.level.name / origem
            if not arquivo.is_file():
                continue
            with arquivo.open(encoding="utf-8", newline="") as fluxo:
                leitor = csv.DictReader(fluxo)
                for nome in leitor.fieldnames or []:
                    if nome not in campos:
                        campos.append(nome)
                for linha in leitor:
                    linha["load_level"] = celula.level.name
                    linha["requests"] = celula.level.requests
                    linha["multiplier"] = celula.level.multiplier
                    linhas.append(linha)
        inicio = ["topology", "load_level", "requests", "multiplier"]
        campos = inicio + [c for c in campos if c not in inicio]
        caminho = raiz / destino
        with caminho.open("w", encoding="utf-8", newline="") as fluxo:
            escritor = csv.DictWriter(fluxo, fieldnames=campos)
            escritor.writeheader()
            escritor.writerows(linhas)
        gerados.append(caminho)
    return gerados


def _git(*args) -> str | None:
    try:
        saida = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True,
            cwd=Path(__file__).resolve().parent,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return saida.stdout.strip()


def info_git() -> dict:
    commit = _git("rev-parse", "HEAD")
    if commit is None:
        return {"commit": None, "arvore_suja": None, "arquivos_modificados": []}
    # results/ fica de fora: saídas de execuções anteriores não sujam a árvore.
    status = _git("status", "--porcelain", "--", ".", ":(exclude)results") or ""
    modificados = [linha for linha in status.splitlines() if linha]
    return {
        "commit": commit,
        "arvore_suja": bool(modificados),
        "arquivos_modificados": modificados[:50],
    }


def _formatar(segundos: float) -> str:
    segundos = int(round(segundos))
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    if horas:
        return f"{horas}h{minutos:02d}m{segundos:02d}s"
    if minutos:
        return f"{minutos}m{segundos:02d}s"
    return f"{segundos}s"


def executar(
    config: ScenarioConfig, celulas: list[Celula], algoritmos, raiz: Path,
    *, seed: int, retomar: bool, metadados: dict, saida=print, relogio=time.perf_counter,
) -> dict:
    """Roda as células em sequência, gravando uma por vez. Devolve o resumo."""
    specs = create_algorithm_specs(tuple(algoritmos), {
        nome: valores for nome, valores in config.parameters.items()
        if nome in algoritmos
    })
    for antigo in raiz.glob(".tmp-*"):
        shutil.rmtree(antigo, ignore_errors=True)
    pendentes, puladas = [], 0
    for celula in celulas:
        if retomar and celula_concluida(raiz, celula, _assinatura(config, celula, specs, seed)):
            puladas += 1
            saida(f"[pulada] {celula.rotulo} já gravada")
        else:
            pendentes.append(celula)

    inicio = relogio()
    peso_total = sum(c.peso for c in pendentes)
    peso_feito = 0
    duracoes = {}
    for indice, celula in enumerate(pendentes, start=1):
        saida(f"[{indice}/{len(pendentes)}] {celula.rotulo} "
              f"({celula.level.requests} requisições, {celula.repetitions} rep.) ...")
        comeco = relogio()
        runs, agregados = executar_celula(
            celula.topology, celula.level, config, specs,
            repetitions=celula.repetitions, seed=seed,
        )
        duracao = relogio() - comeco
        gravar_celula(raiz, celula, runs, agregados, {
            "assinatura": _assinatura(config, celula, specs, seed),
            "duracao_segundos": duracao,
            "tempo_alocacao_segundos": tempos_de_alocacao(runs),
            "concluida_em": datetime.now().isoformat(timespec="seconds"),
        })
        duracoes[celula.rotulo] = duracao
        peso_feito += celula.peso
        decorrido = relogio() - inicio
        restante = decorrido * (peso_total - peso_feito) / peso_feito
        saida(f"    concluída em {_formatar(duracao)} | decorrido {_formatar(decorrido)} "
              f"| ETA {_formatar(restante)}")
    arquivos = consolidar(raiz, celulas)
    total = relogio() - inicio
    metadados.update({"duracao_segundos": total, "celulas_executadas": len(pendentes),
                      "celulas_puladas": puladas})
    return {"executadas": len(pendentes), "puladas": puladas,
            "duracoes": duracoes, "consolidados": arquivos, "total": total}


def _montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Roda a matriz completa de experimentos (sequencial) e grava "
                    "em results/<AAAAMMDD-HHMMSS>/.",
    )
    parser.add_argument("--config", type=Path,
                        default=Path("experiments/configs/default.json"))
    parser.add_argument("--output-root", type=Path, default=Path("results"))
    parser.add_argument("--topologies", nargs="+", choices=TOPOLOGIES)
    parser.add_argument("--algorithms", nargs="+", choices=ALGORITHMS)
    parser.add_argument("--repetitions", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--dry-run", action="store_true",
                        help="Lista o que rodaria, sem rodar nem gravar.")
    parser.add_argument("--resume", nargs="?", const="ultima", metavar="PASTA",
                        help="Retoma uma execução interrompida (padrão: a mais recente "
                             "em --output-root), pulando células já gravadas.")
    parser.add_argument("--estimar", action="store_true",
                        help="Roda a versão reduzida e extrapola o tempo da matriz "
                             "completa (ver experiments/estimativa.py).")
    return parser


def _pasta_para_retomar(raiz: Path, pedido: str) -> Path:
    if pedido != "ultima":
        pasta = Path(pedido)
        return pasta if pasta.exists() else raiz / pedido
    candidatas = sorted(
        p for p in raiz.glob("*") if (p / "config_usada.json").is_file()
        and not p.name.endswith("-estimativa")
    ) if raiz.is_dir() else []
    if not candidatas:
        raise ValueError(f"Nenhuma execução para retomar em {raiz}.")
    return candidatas[-1]


def main(argv=None) -> None:
    parser = _montar_parser()
    args = parser.parse_args(argv)
    try:
        config_path = args.config
        config = load_config(config_path)
        topologias = args.topologies or list(config.topologies)
        desconhecidas = [t for t in topologias if t not in TOPOLOGIES]
        if desconhecidas:
            raise ValueError(f"Topologias desconhecidas: {desconhecidas}")
        algoritmos = args.algorithms or list(config.algorithms)
        repeticoes = args.repetitions or config.repetitions
        seed = config.seed if args.seed is None else args.seed
        retomar = args.resume is not None
        if args.estimar and retomar:
            raise ValueError("--estimar não combina com --resume.")
        if args.estimar:
            celulas = planejar_estimativa(config, topologias)
        else:
            celulas = planejar(config, topologias, repeticoes)

        if args.dry_run:
            _dry_run(args, config, celulas, algoritmos, seed, retomar)
            return

        agora = datetime.now()
        if retomar:
            raiz = _pasta_para_retomar(args.output_root, args.resume)
            salvo = json.loads((raiz / "config_usada.json").read_text(encoding="utf-8"))
            if salvo != json.loads(config_path.read_text(encoding="utf-8")):
                raise ValueError("A config difere da usada na execução a retomar.")
            metadados = json.loads((raiz / "metadados.json").read_text(encoding="utf-8"))
            metadados.setdefault("retomadas", []).append(agora.isoformat(timespec="seconds"))
        else:
            sufixo = "-estimativa" if args.estimar else ""
            raiz = args.output_root / (agora.strftime("%Y%m%d-%H%M%S") + sufixo)
            if raiz.exists():
                raise ValueError(f"A pasta {raiz} já existe; tente de novo.")
            raiz.mkdir(parents=True)
            shutil.copyfile(config_path, raiz / "config_usada.json")
            metadados = {
                "data_hora": agora.isoformat(timespec="seconds"),
                "python": sys.version,
                "plataforma": platform.platform(),
                "git": info_git(),
                "config": str(config_path),
                "seed": seed,
                "sobrescritas": {
                    "topologias": args.topologies, "algoritmos": args.algorithms,
                    "repeticoes": args.repetitions, "seed": args.seed,
                },
                "algoritmos": algoritmos,
                "modo": "estimativa" if args.estimar else "completo",
                "celulas": [
                    {"topology": c.topology, "load_level": c.level.name,
                     "repetitions": c.repetitions} for c in celulas
                ],
            }
        _gravar_metadados(raiz, metadados)
        print(f"Saída: {raiz.resolve()}")
        resumo = executar(config, celulas, algoritmos, raiz, seed=seed,
                          retomar=retomar, metadados=metadados)
        _gravar_metadados(raiz, metadados)
        if args.estimar:
            from experiments.estimativa import imprimir_estimativa
            imprimir_estimativa(raiz, config, topologias, algoritmos)
    except (ValueError, TypeError, OSError, KeyError) as erro:
        parser.error(str(erro))
    print(f"Concluído em {_formatar(resumo['total'])}: "
          f"{resumo['executadas']} células rodadas, {resumo['puladas']} puladas.")
    print(f"Resultados: {raiz.resolve()}")


def _gravar_metadados(raiz: Path, metadados: dict) -> None:
    (raiz / "metadados.json").write_text(
        json.dumps(metadados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _dry_run(args, config, celulas, algoritmos, seed, retomar) -> None:
    specs = create_algorithm_specs(tuple(algoritmos), {
        n: v for n, v in config.parameters.items() if n in algoritmos})
    raiz = None
    if retomar:
        try:
            raiz = _pasta_para_retomar(args.output_root, args.resume)
        except ValueError:
            raiz = None
    print(f"[dry-run] seed={seed} | algoritmos: {', '.join(algoritmos)}")
    total_execs = 0
    for celula in celulas:
        pulada = raiz is not None and celula_concluida(
            raiz, celula, _assinatura(config, celula, specs, seed))
        execs = celula.repetitions * len(algoritmos)
        total_execs += 0 if pulada else execs
        print(f"  {'pularia' if pulada else 'rodaria'} {celula.rotulo:<24} "
              f"{celula.level.requests:>3} requisições x{celula.level.multiplier} "
              f"| {celula.repetitions} rep. x {len(algoritmos)} alg. = {execs} execuções")
    print(f"[dry-run] {len(celulas)} células, {total_execs} execuções de algoritmo. "
          "Nada foi executado nem gravado.")


if __name__ == "__main__":
    main()
