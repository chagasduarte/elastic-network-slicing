"""Diagnóstico (somente leitura) do custo do SA em redes maiores.

Executa o SA com os parâmetros finais da monografia em poucas requisições do
nível l6 (80 x 4,0, semente de cenário 42, a mesma da matriz) em GÉANT e
Germany50, sob cProfile, e imprime: tempo por alocação, contadores do SA
(vizinhos gerados, chamadas à busca de sufixo, avaliações de custo) e as
funções que mais consomem tempo. NÃO altera nenhum algoritmo: usa só os
contadores externos de scripts/calibracao/common.py e o cProfile da stdlib.

Uso: python3.11 -m scripts.diagnostico_sa_germany50 [--requisicoes N]
Rode com a máquina ociosa (LOCK_EXPERIMENTO em notas/coordenacao/).
"""
import argparse
import cProfile
import io
import pstats
import time

from scripts.calibracao.common import build_requests, run_one

SA = {"initial_temperature": 0.25, "minimum_temperature": 0.001,
      "cooling_rate": 0.9463, "max_iterations": 100}


def diagnosticar(topologia, n_requisicoes):
    requests = build_requests(topologia, 80, 4.0, 42)[:n_requisicoes]
    perfil = cProfile.Profile()
    inicio = time.perf_counter()
    perfil.enable()
    run, contadores = run_one(topologia, requests, "sa", SA, 42)
    perfil.disable()
    total = time.perf_counter() - inicio
    ms = [m.elapsed_seconds * 1000 for m in run.measurements]
    print(f"\n== {topologia}: {len(requests)} requisições x 4 períodos "
          f"({len(ms)} alocações), tempo total sob cProfile {total:.1f} s")
    print(f"tempo por alocação (ms, sob cProfile): média {sum(ms)/len(ms):.1f}, "
          f"mín {min(ms):.1f}, máx {max(ms):.1f}")
    print("contadores médios por busca:",
          {k: round(v, 1) for k, v in contadores.items()})
    saida = io.StringIO()
    pstats.Stats(perfil, stream=saida).sort_stats("tottime").print_stats(8)
    print("\n".join(saida.getvalue().splitlines()[:24]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--requisicoes", type=int, default=4)
    args = parser.parse_args()
    for topologia in ("geant", "germany50"):
        diagnosticar(topologia, args.requisicoes)


if __name__ == "__main__":
    main()
