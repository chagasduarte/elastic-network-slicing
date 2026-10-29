"""Salva as decisões (caminhos) de PETIC e Q-Learning num cenário fixo.

Prova de não regressão: rodar antes e depois de mudar os defaults de ACO/SA e
comparar os arquivos. Uso: python3.11 -m scripts.calibracao.regressao_decisoes SAIDA.json
"""
import json
import sys

from scripts.calibracao.common import build_requests, run_one


def main(out):
    result = {}
    for topology, n, mult in (("nobel-germany", 12, 2.5), ("abilene", 10, 3.0)):
        requests = build_requests(topology, n, mult, scenario_seed=777)
        for algorithm in ("petic", "q-learning"):
            run, _ = run_one(topology, requests, algorithm, None, seed=42, count=False)
            result[f"{topology}:{algorithm}"] = [
                [m.request_id, m.period, m.accepted, list(m.path)]
                for m in run.measurements
            ]
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
