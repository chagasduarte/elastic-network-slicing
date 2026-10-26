# CLAUDE.md

## Contexto

Simulador em Python do TCC de Ciência da Computação (UVA, 2026), "Alocação dinâmica de recursos para formação de fatias de rede em ambientes de demanda elástica". Compara quatro alocadores: PETIC, ACO, Simulated Annealing (SA) e Q-Learning, em topologias de grafo, com demandas de banda que variam por período.

Documentos do TCC em `docs/tcc/`: `metodologia.tex` (capítulo escrito, com trechos `[PENDENTE]`), `REVISAO_CODIGO.md` (problemas por prioridade) e `PROMPT_MAESTRI.md` (plano de fases).

## Arquitetura

- `domain/`: nós, enlaces, grafo (`NetworkGraph`), requisições, demandas e resultados.
- `algorithms/`: `petic/`, `aco/`, `sa/`, `q_learning/`, cada um com seu alocador.
- `contracts/`: interfaces abstratas (`SliceAllocator`, `PathFinder`, ...) e construção das topologias.
- `pathfinding/`, `services/`: Dijkstra e reserva de banda (`BandwidthReservationService`).
- `metrics/`: coleta, cálculo, agregação e exportação das métricas.
- `experiments/`: `runner.py` (execução e repetições) e `cli.py` (comparação dos alocadores).
- `main.py`: execução de uma requisição; `create_allocator` centraliza a construção dos alocadores.

A escolha do caminho (alocador) e a reserva de banda (serviço) são etapas separadas. A capacidade é contabilizada por período (`demand_id`).

## Comandos

Use Python 3.10 ou superior (nesta máquina, `python3.11`; o `python3` do sistema é 3.9 e não roda o código).

```bash
python3.11 -m unittest discover -s tests          # testes (devem passar antes de cada commit)
python3.11 -m experiments.cli --help              # experimentos
python3.11 main.py --algorithm petic --seed 42    # execução simples
```

## Convenções

- Python 3.10; o núcleo usa só a biblioteca padrão. Dependências extras (scipy, matplotlib) apenas em `requirements-dev.txt`.
- Nomes e mensagens em português, como já estão no código.
- Tudo reprodutível por semente.

## Regras de trabalho

- Branch `tcc-estrutura`; um commit por fase. Rode os testes antes de cada commit.
- Ao fim de cada fase, pare, resuma o que mudou e espere o OK do autor.
- Nunca inventar dados, números ou referências; se faltar decisão, perguntar.
- Não alterar o comportamento de nenhum algoritmo (escolha de caminho, custos, parâmetros) sem perguntar: o texto do TCC o descreve.
- A regra de reaproveitamento do PETIC só muda após o autor conferir Gomes et al. (2018).
- O texto de Resultados usa somente dados gerados em `results/`, citando o arquivo de origem em comentário LaTeX.
