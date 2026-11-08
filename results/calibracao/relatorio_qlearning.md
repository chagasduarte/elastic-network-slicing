# Calibração do Q-Learning (varredura curta de sensibilidade)

Todos os números vêm de arquivos em `results/calibracao/` (gerados por `scripts/calibracao/`). Nenhum default em `algorithms/q_learning` nem o README foi alterado: o texto abaixo só **propõe**; a escolha é do autor.

## Método
- Mesmo método de ACO/SA: cenários com semente 1001, execuções 1000..1004 (nada de seed 42 nem de `default.json`); 3 cenários (nobel-germany 60×3.0, nobel-germany 80×4.0, abilene 80×4.0; capacidade 800, base 40, ruído 0.3, perfil 0.25/0.5/0.75/1.0) → n=15 pares por configuração.
- Fixos: `discount_factor=1.0`, `path_change_penalty=0.15`.
- Diferença pareada (mesmo cenário e semente) contra a base, com erro-padrão (`pareado.py`).
- Tempos da varredura (`ms*`, 8 processos em paralelo) são só indicativos; o tempo final vem de `medicao_tempo.py`, sequencial.
- Rodado somente depois que o `run_all` terminou (pgrep vazio).

## Orçamento
O custo do Q-Learning é linear em `episodes` (≈ `avaliados` por alocação ≈ episódios; `expansoes` cresce com a duração dos episódios, que depende de `epsilon_decay`). Varreu-se `episodes` ∈ {250, 500, 1000, 2000, 4000}; em 1000 episódios, `learning_rate` ∈ {0.1, 0.2, 0.5} × `epsilon_decay` ∈ {0.99, 0.995, 0.999} (9 combinações). Nada foi cortado do grid pedido; cada varredura levou ~1–2 min.

## Varredura 1: episódios (base: episodes=2000, default)
Fonte: `resumo_ql1.csv`, `pareado_ql1.csv`.

| config | banda atendida | Δ pareado (EP) | aceitação | util. máx. % | Jain/período | saltos | tempo seq. (ms, média) |
|---|---|---|---|---|---|---|---|
| petic | 0.6497 | +0.0011 (0.0004) | 0.740 | 99.8 | 0.8582 | 2.586 | 0.075 |
| ep250 | 0.6512 | +0.0026 (0.0011) | 0.741 | 99.7 | 0.8594 | 2.599 | 2.81 |
| ep500 | 0.6505 | +0.0020 (0.0011) | 0.741 | 99.6 | 0.8576 | 2.593 | 3.55 |
| ep1000 | 0.6486 | 0.0000 (0) | 0.740 | 99.7 | 0.8573 | 2.592 | 5.68 |
| ep2000 (default) | 0.6486 | base | 0.740 | 99.7 | 0.8573 | 2.592 | 9.78 |
| ep4000 | 0.6486 | 0.0000 (0) | 0.740 | 99.7 | 0.8573 | 2.592 | 19.03 |

Tempo: `tempo_ql.csv` (sequencial, 2 topologias × 3 sementes, 1680 alocações por linha).

## Varredura 2: learning_rate × epsilon_decay (episodes=1000; base lr0.2_ed0.995)
Fonte: `resumo_ql2.csv`, `pareado_ql2.csv`.

| config | banda atendida | Δ pareado (EP) | Jain | saltos | ms* (paralelo) |
|---|---|---|---|---|---|
| lr0.1_ed0.99 | 0.6494 | +0.0009 (0.0010) | 0.8574 | 2.595 | 17.6 |
| lr0.1_ed0.995 | 0.6509 | +0.0024 (0.0011) | 0.8573 | 2.594 | 19.1 |
| lr0.1_ed0.999 | 0.6486 | 0 | 0.8573 | 2.592 | 31.8 |
| lr0.2_ed0.99 | 0.6486 | 0 | 0.8573 | 2.592 | 16.3 |
| lr0.2_ed0.995 | 0.6486 | base | 0.8573 | 2.592 | 18.4 |
| lr0.2_ed0.999 | 0.6486 | 0 | 0.8573 | 2.592 | 32.1 |
| lr0.5_ed0.99 | 0.6486 | 0 | 0.8573 | 2.592 | 18.7 |
| lr0.5_ed0.995 | 0.6486 | 0 | 0.8573 | 2.592 | 24.5 |
| lr0.5_ed0.999 | 0.6486 | 0 | 0.8573 | 2.592 | 37.7 |

Aceitação e utilização máxima praticamente idênticas em todas as linhas (0.740–0.741; 99.6–99.7 %); ver os CSVs.

## Comparação com o PETIC (`comparacao_petic_ql.csv`, `comparacao_petic.py`)
Por alocação, no mesmo estado do grafo, 3200 alocações com caminho de ambos (3206 em ep250/ep500). Custo = soma de exp(b/a) dos enlaces, sem penalidade nem bônus de reaproveitamento; "mínimo" = Dijkstra exato com esse custo.

| config | mesmo caminho do PETIC | custo ótimo (= mínimo) | custo a mais vs PETIC | custo a mais vs mínimo |
|---|---|---|---|---|
| ep250 | 96.72 % | 97.50 % | +0.022 % | +0.023 % |
| ep500 | 96.44 % | 97.63 % | +0.023 % | +0.024 % |
| ep1000 | 97.19 % | 97.50 % | +0.012 % | +0.013 % |
| ep2000 | 97.19 % | 97.50 % | +0.012 % | +0.013 % |
| ep4000 | 97.19 % | 97.50 % | +0.012 % | +0.013 % |

(Excesso = média por alocação da razão custo_QL/custo_ref − 1, agregada sobre as 15 execuções.) Em ≈2,5 % das alocações o Q-Learning não acha o caminho de custo mínimo; nessas, o custo a mais é pequeno.

## Joelho
A qualidade (banda atendida, aceitação, Jain, saltos, utilização) estabiliza em **1000 episódios**: ep1000 = ep2000 = ep4000 exatamente (diferença 0), e a fração de caminhos iguais ao PETIC/mínimo também. Abaixo disso, ep250/ep500 diferem ≤ +0.0026 de banda (≈1,8–2,5 EP, com sinal *positivo*, ou seja, ruído e não perda) e acham o mínimo um pouco menos vezes (96,4–96,7 % vs 97,2 % de igualdade ao PETIC). Tempo sequencial cai de 9,78 ms (2000) para 5,68 ms (1000) e 3,55 ms (500). Em `learning_rate` e `epsilon_decay` não há sensibilidade mensurável em banda: só custo; `epsilon_decay` maior prolonga a exploração e o tempo (ed0.999 ≈ 1,7× o tempo de ed0.99 no paralelo).

## Parâmetros propostos (decisão do autor)
- `episodes`: 1000 (resultados iguais aos de 2000/4000 e metade do tempo: 5,68 vs 9,78 ms). Alternativa conservadora: manter 2000 (default atual), sem perda de qualidade, só mais tempo.
- `learning_rate` 0.2 e `epsilon_decay` 0.995: manter; o grid não achou ganho. Variações com diferença ≠ 0 (lr0.1_ed0.995, +0.0024, 2,2 EP) não são robustas e não justificam troca.
- Observação para o texto do TCC: o tempo de decisão do Q-Learning default (9,78 ms) fica próximo do ACO (9,95 ms) em `tempo_final.csv`; com 1000 episódios (5,68 ms) deixa de ser comparável. Se o objetivo for igualar tempos como foi feito com o SA, isso afeta a escolha.

## Limites
- Só três cenários saturados e 5 sementes; diferenças < ~2 EP não são distinguíveis de ruído. A banda atendida é quase idêntica ao PETIC em todos os casos (o Q-Learning aprende essencialmente o caminho de custo mínimo; este cenário não separa os algoritmos).
- Tabela Q reiniciada a cada alocação, logo `episodes` é por alocação.
- Excesso de custo é razão média por alocação, sem a penalidade de troca de caminho do Q-Learning (a comparação é em custo exp(b/a) puro).
- Tempos paralelos (`ms*`) não são comparáveis aos de `tempo_ql.csv`; o tempo sequencial rodou com a máquina sem processos de experimento, mas com navegador e interface gráfica abertos.
- Os tempos de PETIC/ACO/SA citados vêm de `tempo_final.csv` (medição anterior), não foram remedidos aqui.

## Commits (branch qlearning-calibracao)
- 46557f2: grade de episódios e `comparacao_petic.py`
- 53151d6: resultados (varreduras, comparação, tempos) e grades ql2/tempo
- relatório: commit seguinte
Testes: `python3.11 -m unittest discover -s tests` → 149 testes, OK.
