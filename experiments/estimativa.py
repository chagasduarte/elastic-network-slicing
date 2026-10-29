"""Extrapolação do tempo da matriz completa a partir de células medidas.

Lê os `celula.json` de uma execução reduzida (`run_all --estimar`) e estima o
tempo da matriz da config: por (topologia, nível, algoritmo), o tempo de
allocate por repetição é o medido, ou interpolado linearmente pelo número de
requisições entre as células medidas da mesma topologia. A incerteza é o
intervalo [mínimo, máximo] entre os vizinhos medidos (limites inferior e
superior) e não inclui a variância entre repetições, estimada com poucas
repetições. Só usa tempos efetivamente medidos.
"""

import json
from pathlib import Path

from experiments.scenarios import ScenarioConfig


def ler_medicoes(raiz: Path) -> dict:
    """{(topologia, nível): {'requests', 'reps', 'duracao', 'alocacao': {alg: s}}}"""
    medicoes = {}
    for marcador in raiz.glob("*/*/celula.json"):
        dados = json.loads(marcador.read_text(encoding="utf-8"))
        ass = dados["assinatura"]
        medicoes[(ass["topology"], ass["load_level"])] = {
            "requests": ass["requests"],
            "reps": ass["repetitions"],
            "duracao": dados["duracao_segundos"],
            "alocacao": dados["tempo_alocacao_segundos"],
        }
    return medicoes


def _por_repeticao(medicao: dict, algoritmo: str) -> float:
    return medicao["alocacao"][algoritmo] / medicao["reps"]


def _sobrecarga_por_rep(medicao: dict) -> float:
    return (medicao["duracao"] - sum(medicao["alocacao"].values())) / medicao["reps"]


def _interpolar(pontos: list[tuple[int, float]], x: int) -> tuple[float, float, float]:
    """(central, baixo, alto) a partir de pontos (requisições, valor) medidos."""
    pontos = sorted(pontos)
    for xi, yi in pontos:
        if xi == x:
            return yi, yi, yi
    abaixo = [p for p in pontos if p[0] < x]
    acima = [p for p in pontos if p[0] > x]
    if abaixo and acima:
        (x0, y0), (x1, y1) = abaixo[-1], acima[0]
        central = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return central, min(y0, y1), max(y0, y1)
    # Fora da faixa medida: extrapola proporcionalmente ao ponto mais próximo.
    xi, yi = (abaixo[-1] if abaixo else acima[0])
    central = yi * x / xi
    return central, min(yi, central), max(yi, central)


def extrapolar(medicoes: dict, config: ScenarioConfig, topologias, algoritmos) -> dict:
    """Devolve {'celulas': {(top, nivel, alg): (c, b, a) por rep},
    'total': {alg: (c, b, a)}, 'sobrecarga': (c, b, a), 'geral': (c, b, a)}."""
    celulas, total = {}, {alg: [0.0, 0.0, 0.0] for alg in algoritmos}
    sobre = [0.0, 0.0, 0.0]
    for topologia in topologias:
        medidas = {n: m for (t, n), m in medicoes.items() if t == topologia}
        if not medidas:
            raise ValueError(f"Sem medições para {topologia}.")
        for nivel in config.load_levels:
            for alg in algoritmos:
                pontos = [(m["requests"], _por_repeticao(m, alg)) for m in medidas.values()]
                estimativa = _interpolar(pontos, nivel.requests)
                celulas[(topologia, nivel.name, alg)] = estimativa
                for i in range(3):
                    total[alg][i] += estimativa[i] * config.repetitions
            pontos = [(m["requests"], _sobrecarga_por_rep(m)) for m in medidas.values()]
            estimativa = _interpolar(pontos, nivel.requests)
            for i in range(3):
                sobre[i] += estimativa[i] * config.repetitions
    geral = [sum(total[a][i] for a in algoritmos) + sobre[i] for i in range(3)]
    return {"celulas": celulas, "total": {a: tuple(v) for a, v in total.items()},
            "sobrecarga": tuple(sobre), "geral": tuple(geral)}


def _fmt(segundos: float) -> str:
    if segundos >= 3600:
        return f"{segundos / 3600:.2f} h"
    if segundos >= 60:
        return f"{segundos / 60:.1f} min"
    return f"{segundos:.2f} s"


def imprimir_estimativa(raiz: Path, config: ScenarioConfig, topologias, algoritmos) -> None:
    medicoes = ler_medicoes(raiz)
    print("\nTempos medidos (s de allocate por repetição, por algoritmo):")
    print(f"{'topologia':<14}{'nível':<6}{'req':>4}{'rep':>4}  "
          + "".join(f"{a:>12}" for a in algoritmos) + f"{'sobrecarga':>12}")
    for (topologia, nivel), m in sorted(medicoes.items()):
        print(f"{topologia:<14}{nivel:<6}{m['requests']:>4}{m['reps']:>4}  "
              + "".join(f"{_por_repeticao(m, a):>12.3f}" for a in algoritmos)
              + f"{_sobrecarga_por_rep(m):>12.3f}")
    try:
        resultado = extrapolar(medicoes, config, topologias, algoritmos)
    except ValueError as erro:
        print(f"Extrapolação indisponível: {erro}")
        return
    print(f"\nExtrapolação para a matriz completa ({config.repetitions} repetições, "
          "central [baixo; alto]):")
    for alg in algoritmos:
        c, b, a = resultado["total"][alg]
        print(f"  {alg:<12}{_fmt(c):>10}  [{_fmt(b)}; {_fmt(a)}]")
    c, b, a = resultado["sobrecarga"]
    print(f"  {'sobrecarga':<12}{_fmt(c):>10}  [{_fmt(b)}; {_fmt(a)}]")
    c, b, a = resultado["geral"]
    print(f"  {'TOTAL':<12}{_fmt(c):>10}  [{_fmt(b)}; {_fmt(a)}]")
    ranking = sorted(
        ((chave, v[0] * config.repetitions) for chave, v in resultado["celulas"].items()),
        key=lambda item: -item[1],
    )[:8]
    print("\nCélulas que mais pesam (topologia, nível, algoritmo):")
    for (topologia, nivel, alg), segundos in ranking:
        print(f"  {topologia}/{nivel}/{alg}: {_fmt(segundos)}")
    destino = raiz / "estimativa.json"
    destino.write_text(json.dumps({
        "repeticoes": config.repetitions,
        "total_por_algoritmo": {a: list(v) for a, v in resultado["total"].items()},
        "sobrecarga": list(resultado["sobrecarga"]),
        "geral": list(resultado["geral"]),
        "celulas": {"/".join(k): list(v) for k, v in resultado["celulas"].items()},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
