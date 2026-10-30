"""Figuras (PDF) e tabelas LaTeX (abnTeX2) dos resultados de uma matriz de experimentos.

Uso:
    python3.11 -m scripts.plots --run results/20261029-224824

Saídas: <run>/figuras/*.pdf e <run>/tabelas/*.tex. Todo número vem de
<run>/todos_agregados.csv (escopo "summary"); nada é calculado ou arredondado
além da formatação de exibição.

Nota estatística: cada repetição é um conjunto independente de requisições;
os algoritmos compartilham o conjunto dentro de cada cenário. Média, desvio e
IC 95% são calculados entre cenários (n=30 na matriz principal).

Rótulos \\label das tabelas: tab:<aceitacao|banda|tempo>-<topologia>
(ex.: tab:aceitacao-abilene, tab:banda-geant, tab:tempo-nobel-germany).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
matplotlib.rcParams["font.family"] = "DejaVu Sans"

ALGORITMOS = ["petic", "aco", "sa", "q-learning"]
NOMES_ALGORITMO = {"petic": "PETIC", "aco": "ACO", "sa": "SA", "q-learning": "Q-Learning"}
# Okabe-Ito (daltônicos) + marcadores e traços distintos (legível em preto e branco).
ESTILOS = {
    "petic": dict(color="#000000", marker="o", linestyle="-"),
    "aco": dict(color="#D55E00", marker="s", linestyle="--"),
    "sa": dict(color="#0072B2", marker="^", linestyle="-."),
    "q-learning": dict(color="#009E73", marker="D", linestyle=":"),
}
NOMES_TOPOLOGIA = {"abilene": "Abilene", "nobel-germany": "Nobel-Germany", "geant": "GÉANT"}

# nome do arquivo -> (coluna base, rótulo do eixo y, escala log)
METRICAS = {
    "aceitacao": ("acceptance.acceptance_percent", "Aceitação (%)", False),
    "banda_atendida": ("bandwidth.served_percent", "Banda atendida (%)", False),
    "utilizacao_media": ("network.average_utilization_percent", "Utilização média (%)", False),
    "utilizacao_maxima": ("network.max_utilization_percent", "Utilização máxima (%)", False),
    "enlaces_saturados_80": ("network.saturated_links_80", "Enlaces com uso $\\geq$ 80% (nº)", False),
    "enlaces_saturados_90": ("network.saturated_links_90", "Enlaces com uso $\\geq$ 90% (nº)", False),
    "enlaces_saturados_100": ("network.saturated_links", "Enlaces com uso = 100% (nº)", False),
    "jain": ("network.fairness_jain_period_mean", "Índice de Jain (média dos períodos)", False),
    "saltos_medios": ("paths.mean_hops", "Saltos médios por caminho", False),
    "reutilizacao": ("path_changes.reuse_rate", "Taxa de reutilização de caminho", False),
    "tempo_decisao": ("timing.total_seconds", "Tempo total de decisão (s)", True),
}

NOTA_TEMPO = (
    "Barras: IC 95% entre cenários independentes (n={n}); tempo de CPU de allocate, "
    "escala logarítmica."
)
NOTA_ESTATISTICA = (
    "Barras: IC 95% entre cenários independentes (n={n}); algoritmos pareados por cenário."
)


# ---------------------------------------------------------------- leitura

def _num(texto: str | None) -> float | None:
    if texto is None:
        return None
    texto = texto.strip()
    if texto == "" or texto.lower() in ("nan", "none"):
        return None
    try:
        valor = float(texto)
    except ValueError:
        return None
    return None if valor != valor else valor


def ler_agregados(caminho: Path) -> list[dict]:
    """Linhas do escopo 'summary' de todos_agregados.csv, com colunas como strings."""
    with open(caminho, newline="", encoding="utf-8") as f:
        return [linha for linha in csv.DictReader(f) if linha["scope"] == "summary"]


def estatistica(linha: dict, base: str) -> dict:
    """mean, stddev, ci95_low, ci95_high (None quando vazio/NaN/ausente)."""
    return {k: _num(linha.get(f"{base}.{k}")) for k in ("mean", "stddev", "ci95_low", "ci95_high")}


def niveis_da_config(run: Path) -> list[dict]:
    with open(run / "config_usada.json", encoding="utf-8") as f:
        return json.load(f)["load_levels"]


def formatar_numero(valor: float | None, casas: int, virgula: bool = True) -> str:
    """Formata com número fixo de casas; vírgula decimal (pt-BR); None vira '--'."""
    if valor is None:
        return "--"
    texto = f"{valor:.{casas}f}"
    return texto.replace(".", ",") if virgula else texto


# ---------------------------------------------------------------- figuras

def _indice(linhas: list[dict]) -> dict:
    return {(l["topology"], l["load_level"], l["algorithm"]): l for l in linhas}


def figura_metrica(linhas: list[dict], niveis: list[dict], topologias: list[str],
                   base: str, ylabel: str, log: bool, destino: Path) -> None:
    """Um painel com uma coluna por topologia; eixo x = nível de carga."""
    idx = _indice(linhas)
    ns = [_num(l.get(f"{base}.count")) for l in linhas]
    n_cenarios = max((int(n) for n in ns if n is not None), default=0)
    fig, eixos = plt.subplots(1, len(topologias), figsize=(6.5, 3.4), sharey=False, squeeze=False)
    eixos = eixos[0]
    n = len(ALGORITMOS)
    desloc = [(i - (n - 1) / 2) * 0.07 for i in range(n)]
    for ax, topo in zip(eixos, topologias):
        for i, alg in enumerate(ALGORITMOS):
            xs, ys, lo, hi = [], [], [], []
            for k, nivel in enumerate(niveis):
                linha = idx.get((topo, nivel["name"], alg))
                if linha is None:
                    continue
                e = estatistica(linha, base)
                if e["mean"] is None:
                    continue
                xs.append(k + desloc[i])
                ys.append(e["mean"])
                bi, bs = e["ci95_low"], e["ci95_high"]
                sem_barra = bi is None or bs is None or (bi == e["mean"] and bs == e["mean"])
                lo.append(0.0 if sem_barra else max(e["mean"] - bi, 0.0))
                hi.append(0.0 if sem_barra else max(bs - e["mean"], 0.0))
            ax.errorbar(xs, ys, yerr=[lo, hi], label=NOMES_ALGORITMO[alg], markersize=4,
                        linewidth=1.0, capsize=2, elinewidth=0.8, **ESTILOS[alg])
        ax.set_title(NOMES_TOPOLOGIA.get(topo, topo), fontsize=9)
        ax.set_xticks(range(len(niveis)))
        ax.set_xticklabels([f"{nv['name']}\n{nv['requests']}\n×{formatar_numero(float(nv['multiplier']), 1)}"
                            for nv in niveis], fontsize=5)
        ax.set_xlabel("Nível (requisições, multiplicador)", fontsize=6)
        ax.tick_params(axis="y", labelsize=7)
        if log:
            ax.set_yscale("log")
        ax.grid(True, linewidth=0.3, alpha=0.6)
    eixos[0].set_ylabel(ylabel, fontsize=8)
    handles, rotulos = eixos[0].get_legend_handles_labels()
    fig.legend(handles, rotulos, loc="lower center", ncol=n, fontsize=8, frameon=False,
               bbox_to_anchor=(0.5, 0.035))
    nota = NOTA_TEMPO if log else NOTA_ESTATISTICA
    fig.text(0.5, 0.012, nota.format(n=n_cenarios), ha="center", fontsize=5.5)
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, format="pdf", metadata={"Creator": "scripts.plots", "Producer": "matplotlib",
                                                 "CreationDate": None, "ModDate": None})
    plt.close(fig)


# ---------------------------------------------------------------- tabelas

TABELAS = {
    "aceitacao": ("acceptance.acceptance_percent", 2,
                  "Aceitação (\\%) na topologia {topo}: média $\\pm$ desvio-padrão amostral [IC 95\\%]"),
    "banda": ("bandwidth.served_percent", 2,
              "Banda atendida (\\%) na topologia {topo}: média $\\pm$ desvio-padrão amostral [IC 95\\%]"),
    "tempo": ("timing.total_seconds", 4,
              "Tempo total de decisão (s) na topologia {topo}: média $\\pm$ desvio-padrão amostral [IC 95\\%]"),
}


def celula(e: dict, casas: int) -> tuple[str, str]:
    f = lambda v: formatar_numero(v, casas)  # noqa: E731
    media = f"{f(e['mean'])} $\\pm$ {f(e['stddev'])}"
    ic = "--" if e["ci95_low"] is None or e["ci95_high"] is None else f"[{f(e['ci95_low'])}; {f(e['ci95_high'])}]"
    return media, ic


def tabela_latex(linhas: list[dict], niveis: list[dict], topo: str, chave: str, caminho_csv: str) -> str:
    base, casas, titulo = TABELAS[chave]
    idx = _indice(linhas)
    rotulo = f"tab:{chave}-{topo}"
    out = [
        f"% fonte: {caminho_csv}, colunas {base}.mean, {base}.stddev, {base}.ci95_low, {base}.ci95_high",
        "% escopo summary; unidade amostral: cenário independente; desvio-padrão amostral (n-1) e IC 95% entre cenários.",
        ("% tempo de CPU medido apenas durante allocate." if chave == "tempo" else
         "% os algoritmos compartilham as requisições em cada cenário."),
        "\\begin{table}[htb]",
        "    \\centering",
        "    \\small",
        f"    \\caption{{{titulo.format(topo=NOMES_TOPOLOGIA.get(topo, topo))}}}",
        f"    \\label{{{rotulo}}}",
        "    \\begin{tabular}{llcc}",
        "        \\hline",
        "        Nível (req.$\\times$mult.) & Algoritmo & Média $\\pm$ desvio & IC 95\\% \\\\",
        "        \\hline",
    ]
    for nivel in niveis:
        rot_nivel = f"{nivel['name']} ({nivel['requests']}$\\times${formatar_numero(float(nivel['multiplier']), 1)})"
        for i, alg in enumerate(ALGORITMOS):
            linha = idx.get((topo, nivel["name"], alg))
            if linha is None:
                continue
            media, ic = celula(estatistica(linha, base), casas)
            out.append(f"        {rot_nivel if i == 0 else ''} & {NOMES_ALGORITMO[alg]} & {media} & {ic} \\\\")
        out.append("        \\hline")
    out += [
        "    \\end{tabular}",
        "    \\fonte{Elaborado pelo autor.}",
        "\\end{table}",
        "",
    ]
    return "\n".join(out)


def tabela_periodos(linhas: list[dict], niveis: list[dict], topo: str,
                    caminho_csv: str) -> str:
    """Aceitação e banda atendida separadas por período, sem mistura de cargas."""
    periodos = sorted({l["period"] for l in linhas
                       if l["topology"] == topo and l.get("period") not in (None, "")})
    indice = {(l["load_level"], l["algorithm"], l["period"]): l for l in linhas
              if l["topology"] == topo and l.get("period") not in (None, "")}
    out = [
        f"% fonte: {caminho_csv}; scope=period, acceptance.acceptance_percent.mean, bandwidth.served_percent.mean",
        "% unidade amostral: cenário independente; valores separados por período.",
        "\\begin{table}[htb]", "    \\centering", "    \\scriptsize",
        f"    \\caption{{Aceitação e banda atendida por período em {NOMES_TOPOLOGIA.get(topo, topo)} (\\%)}}",
        f"    \\label{{tab:periodos-{topo}}}",
        "    \\begin{tabular}{llr r}", "        \\hline",
        "        Nível & Algoritmo & Aceitação & Banda atendida \\", "        \\hline",
    ]
    for nivel in niveis:
        for alg in ALGORITMOS:
            for periodo in periodos:
                linha = indice.get((nivel["name"], alg, periodo))
                if linha is None:
                    continue
                ace = _num(linha.get("acceptance.acceptance_percent.mean"))
                banda = _num(linha.get("bandwidth.served_percent.mean"))
                rotulo = f"{nivel['name']}, {periodo}"
                out.append(f"        {rotulo} & {NOMES_ALGORITMO[alg]} & {formatar_numero(ace, 2)} & {formatar_numero(banda, 2)} \\")
        out.append("        \\hline")
    out += ["    \\end{tabular}", "    \\fonte{Elaborado pelo autor.}", "\\end{table}", ""]
    return "\n".join(out)


# ---------------------------------------------------------------- CLI

def gerar(run: Path) -> tuple[list[Path], list[Path]]:
    csv_path = run / "todos_agregados.csv"
    linhas = ler_agregados(csv_path)
    with csv_path.open(encoding="utf-8", newline="") as fluxo:
        linhas_todas = list(csv.DictReader(fluxo))
    niveis = niveis_da_config(run)
    topologias = [t for t in NOMES_TOPOLOGIA if any(l["topology"] == t for l in linhas)]
    topologias += sorted({l["topology"] for l in linhas} - set(topologias))
    figuras, tabelas = [], []
    for nome, (base, ylabel, log) in METRICAS.items():
        destino = run / "figuras" / f"{nome}.pdf"
        figura_metrica(linhas, niveis, topologias, base, ylabel, log, destino)
        figuras.append(destino)
    (run / "tabelas").mkdir(exist_ok=True)
    for topo in topologias:
        for chave in TABELAS:
            destino = run / "tabelas" / f"{chave}_{topo}.tex"
            destino.write_text(tabela_latex(linhas, niveis, topo, chave, f"{run.as_posix()}/todos_agregados.csv"),
                               encoding="utf-8")
            tabelas.append(destino)
        destino = run / "tabelas" / f"periodos_{topo}.tex"
        destino.write_text(tabela_periodos(linhas_todas, niveis, topo,
                                           f"{run.as_posix()}/todos_agregados.csv"),
                           encoding="utf-8")
        tabelas.append(destino)
    return figuras, tabelas


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gera figuras e tabelas de uma matriz de experimentos.")
    p.add_argument("--run", required=True, type=Path, help="diretório da execução (ex.: results/20261029-224824)")
    args = p.parse_args(argv)
    figuras, tabelas = gerar(args.run)
    for c in figuras + tabelas:
        print(c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
