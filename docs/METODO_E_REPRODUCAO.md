# Método, decisões de projeto e reprodução dos resultados

Este documento explica **como cada algoritmo foi implementado**, **por que foi feito assim**, e dá o **passo a passo para rodar os testes e chegar às conclusões da monografia**. Complementa o `README.md` (que descreve os comandos) e a monografia (que descreve o experimento).

> Documento em revisão. As pendências de verificação no código e nos CSVs de `results/` estão marcadas como **[confirmar]**.

---

## 1. Visão geral

O projeto compara quatro implementações de alocação de fatias de rede com demanda elástica (a banda de cada requisição muda a cada período `t1..t4`):

| Algoritmo | Ideia |
|---|---|
| **PETIC** | Dijkstra com peso `exp(b/a)` por enlace; reaproveita a fatia anterior quando possível. |
| **ACO** | Colônia de formigas que constrói caminhos guiados por feromônio e uma heurística de folga. |
| **SA** | Recozimento simulado sobre caminhos, com função de custo multiobjetivo. |
| **Q-Learning** | Aprende, por episódios, qual vizinho escolher a cada nó para chegar ao destino. |

Todos implementam a mesma interface (`SliceAllocator.allocate(graph, request, demand, previous_result)`) e operam sobre o mesmo grafo e as mesmas regras de capacidade. Assim, **o que muda entre os resultados é a estratégia de decisão**, não o ambiente.

### Modelo comum (por que é assim)

- **Grafo não direcionado**, com a mesma capacidade nos dois sentidos de cada enlace.
- **Capacidade contabilizada por período** (`Link.available_bandwidth_at(demand_id)`): cada período `t` começa com a rede livre das reservas de outros períodos. Isso modela a "demanda elástica" como uma sequência de decisões independentes por período, em que o que liga os períodos é o caminho anterior (reuso/estabilidade). É uma simplificação assumida e declarada como limitação na monografia.
- **Uma requisição = origem, destino e uma demanda por período.** Uma demanda é aceita se existe caminho em que todos os enlaces têm banda disponível ≥ a demanda.
- **Capacidade uniforme (800 Mbps)** em todas as topologias, para que a carga seja comparável. Abilene e GÉANT originais têm capacidades muito maiores e nunca saturariam com demandas de dezenas de Mbps (item 2 da `docs/tcc/REVISAO_CODIGO.md`).

---

## 2. Os algoritmos

### 2.1 PETIC (`algorithms/petic/`)

**Como funciona.** Para cada demanda, calcula-se o peso de cada enlace `e` como `exp(b / a_e)`, em que `b` é a banda pedida e `a_e` a banda disponível no período. Enlaces com `a_e < b` são inviáveis. O caminho é obtido por **Dijkstra** (custo aditivo).

**Reuso.** Se o resultado do período anterior foi aceito e `Bw(t-1) ≥ Bw(t)`, os enlaces desse caminho recebem peso ε = 1e-4, o que faz o Dijkstra preferi-los.

**Por que assim.**
- O peso exponencial penaliza fortemente enlaces já quase cheios, o que espalha carga sem precisar de estado global.
- A regra de reuso foi **conferida com o artigo original** (Gomes et al., 2018, Algoritmo 1, linha 3): reaproveita a fatia quando a banda anterior cobre a nova. O código e o texto foram alinhados a isso.
- É **determinístico** e **exato** para o custo aditivo considerado: serve de referência para medir quanto as outras abordagens se aproximam ou se afastam dele.

### 2.2 ACO (`algorithms/aco/`)

**Parâmetros do código:** 10 formigas × 20 iterações, `alpha = 1`, `beta = 1`, evaporação `rho = 0,1`, feromônio inicial 1, depósito `1 / custo`.

**Como funciona.** Cada formiga parte da origem e escolhe o próximo nó com probabilidade proporcional a `feromônio^alpha × heurística^beta`. A heurística de um enlace é `disponível / demanda` (0 se não cabe), ou seja, favorece folga. Só enlaces viáveis no período entram. A cada iteração ocorre evaporação e depósito de feromônio nos caminhos encontrados, com mais feromônio para caminhos de custo menor (mesmo custo `exp(b/a)` do PETIC). O melhor caminho encontrado é devolvido.

**Por que assim.**
- Usar o mesmo custo aditivo do PETIC permite perguntar: "uma busca estocástica aproxima o ótimo do Dijkstra?".
- O orçamento 10×20 foi mantido após a calibração (`scripts/calibracao/`, `results/calibracao/`; resultados das grades em `pareado_aco*.csv`). **[confirmar]** o motivo exato da escolha nos CSVs antes de citá-lo.
- **O ACO não usa o resultado do período anterior** (`previous_result` é ignorado). É um desenho deliberado (o algoritmo não foi alterado para não mudar o objeto comparado) e é declarado como limitação: a menor reutilização do ACO vem do desenho, não da meta-heurística em si.

### 2.3 Simulated Annealing (`algorithms/sa/`)

**Parâmetros do código:** temperatura inicial 0,25; mínima 0,001; resfriamento geométrico `lambda = 0,9463`; 100 iterações; 30 tentativas de vizinho por iteração; até 20 passos na geração do vizinho.

**Como funciona.** Parte do caminho de menos saltos (Dijkstra por saltos). A cada iteração gera um vizinho (troca um sufixo do caminho por outro viável, via busca recursiva com ordem aleatória), avalia o custo e aceita piores soluções com probabilidade `exp(-Δ/T)` (critério de Metropolis). O custo combina quatro termos:

| Termo | Peso |
|---|---|
| Número de saltos | 0,20 |
| Utilização média dos enlaces | 0,30 |
| Gargalo (utilização máxima) | 0,35 |
| Distância de Jaccard ao caminho anterior | 0,15 |

**Por que assim.**
- O SA é o único que otimiza **equilíbrio de carga** e **estabilidade** explicitamente. Por isso a monografia o trata como a alternativa que troca aceitação por equilíbrio.
- As 100 iterações vêm de uma decisão do autor: com `lambda = 0,95`, a temperatura caía abaixo do mínimo na iteração ~108, então o limite de 500 nunca era atingido. `lambda = 0,9463` faz a temperatura chegar ao mínimo em ~100 iterações, igualando o orçamento nominal à configuração efetiva.
- **Limitação conhecida (diagnóstico exploratório):** em redes grandes (Germany50) o tempo explode porque a geração de vizinhos faz uma busca recursiva; o perfil está em `results/diagnostico_sa/saida_20261030.txt` (cerca de 3,5 mil expansões por busca em GÉANT contra cerca de 1,45 milhão em Germany50). Por isso Germany50 saiu da matriz final e aparece apenas como evidência exploratória de tempo.

### 2.4 Q-Learning (`algorithms/q_learning/`)

**Parâmetros do código:** 2000 episódios; taxa de aprendizado 0,2; fator de desconto 1,0; ε-greedy com ε de 1,0 a 0,05 e decaimento 0,995 por episódio; penalidade 0,15 por enlace novo em relação ao caminho anterior.

**Como funciona.** O **estado é o nó atual** e a **ação é o próximo vizinho** (somente por enlaces viáveis). O custo do enlace é `exp(b/a)` mais a penalidade por enlace novo em relação ao caminho anterior (a recompensa é o oposto desse custo; **[confirmar]** a forma exata em `q_learning_allocator.py`). A tabela Q é **reiniciada a cada alocação**; ao final dos episódios extrai-se o caminho guloso.

**Por que assim.**
- Estado = nó atual mantém a tabela pequena e o custo aditivo (como no Dijkstra), o que permite comparar com PETIC e ACO sob o mesmo critério.
- A tabela é reiniciada para que cada decisão dependa só do estado da rede naquele período, sem aprendizado acumulado entre períodos. Isso torna o Q-Learning, na prática, um **buscador de caminho treinado do zero em cada alocação**; a monografia explicita isso (o texto de fundamentação é mais geral que a implementação).
- Os 2000 episódios foram escolhidos após a calibração (`results/calibracao/relatorio_qlearning.md`) e mantidos por decisão do autor.

### 2.5 O que **não** é comparável (e por isso é dito na monografia)

- PETIC, ACO e Q-Learning compartilham o custo aditivo `exp(b/a)`; o SA usa **outra função objetivo**.
- ACO não tem memória do período anterior; PETIC, SA e Q-Learning têm.
- Os orçamentos de busca diferem (Dijkstra exato; 10 formigas × 20 iterações; 100 iterações do SA; 2000 episódios do Q-Learning).

Por isso a comparação é entre **implementações completas sob condições externas comuns** (mesmas demandas pareadas, topologia e capacidade), e **não** entre famílias de algoritmos.

---

## 3. Experimento

### 3.1 Desenho

- **Topologias:** Abilene, Nobel-Germany e GÉANT (Germany50 foi retirada da matriz por custo do SA).
- **Capacidade:** 800 Mbps em todos os enlaces.
- **Níveis de carga** (`experiments/configs/default.json`):

| Nível | Requisições | Multiplicador |
|---|---|---|
| l1 | 10 | 1,0 |
| l2 | 20 | 1,5 |
| l3 | 40 | 2,0 |
| l4 | 60 | 2,5 |
| l5 | 80 | 3,0 |
| l6 | 80 | 4,0 |

- **Demanda por período:** base 40 Mbps × perfil `t1..t4 = 0,25 / 0,5 / 0,75 / 1,0` × multiplicador do nível × ruído individual de ±30%.
- **Pares origem/destino:** sorteados sempre com origem ≠ destino, a partir de `Random(f"{seed}:{nível}")`. (Esse cuidado evita um bug conhecido do ACO com origem = destino.)
- **30 cenários independentes por célula** (sementes 42 a 71). **Os quatro algoritmos recebem exatamente o mesmo cenário** — isso é o **pareamento**.
- Total: 3 topologias × 6 níveis × 4 algoritmos × 30 cenários = **2.160 simulações**.

### 3.2 Métricas

Aceitação (% de demandas aceitas), banda atendida, utilização média e máxima dos enlaces, enlaces saturados (≥ 80, 90, 100%), índice de Jain por período (média), número de saltos, reutilização do caminho (somente em transições comparáveis) e tempo de decisão (CPU do processo, `process_time`).

### 3.3 Estatística

A unidade observacional é o **cenário**. Para aceitação, compara-se cada algoritmo contra o PETIC, **pareando por cenário**:

- Wilcoxon de postos sinalizados **exato**, bilateral;
- **Holm** sobre a família de 54 comparações (3 algoritmos × 18 células);
- IC 95% bootstrap (10.000 reamostragens) da diferença média, e correlação bisserial por postos como tamanho de efeito.

As demais métricas (Jain, saltos, tempo, reutilização) são **descritivas**: não passaram por teste inferencial, e a monografia diz isso.

---

## 4. Passo a passo para reproduzir

Tudo na pasta `elastic-network-slicing/`.

### 4.1 Preparar o ambiente

```bash
python3.11 -m venv .venv
source .venv/bin/activate                        # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt    # scipy>=1.11, matplotlib>=3.8
```

O simulador e a análise pareada usam só a biblioteca padrão; `scipy` e `matplotlib` são para testes e gráficos.

### 4.2 Rodar os testes

```bash
python -m unittest discover -s tests -v
```

Resultado esperado na versão `versao-integrada-1` mais as correções posteriores: cerca de **164 testes, OK, com 1 teste pulado e 1 falha esperada** (a falha esperada é intencional: ACO com origem = destino). Tempo: poucos segundos.

Para um módulo específico:

```bash
python -m unittest tests.test_petic_allocator -v
python -m unittest tests.test_scenarios -v
python -m unittest tests.test_paired_analysis tests.test_verificacao_estatistica -v
```

### 4.3 Executar um algoritmo isolado (verificação rápida)

```bash
python main.py --algorithm petic
python main.py --algorithm aco --seed 42
python main.py --algorithm sa --seed 42
python main.py --algorithm q-learning --seed 42
```

### 4.4 Rodar a matriz de experimentos

Matriz **reduzida** (rápida, para conferir que o pipeline funciona):

```bash
python -m experiments.run_all --config experiments/configs/small.json --seed 42 --output-root /tmp/ens-small
```

Matriz **completa** da monografia (cerca de 1 hora; a saída vai para `results/<AAAAMMDD-HHMMSS>/`):

```bash
python -m experiments.run_all --config experiments/configs/default.json --seed 42
```

Opções úteis: `--dry-run` (lista a matriz sem executar), `--resume` (retoma células concluídas), `--estimar` (estima o tempo total com uma versão reduzida).

> Os tempos de CPU dependem da máquina e da carga dela; por isso os valores absolutos de tempo não devem ser comparados entre computadores, apenas entre algoritmos na mesma execução.

### 4.5 Analisar e gerar os produtos

Substitua `<RUN>` pela pasta da execução (a publicada na monografia é `results/20261030-205754`).

```bash
# 1) comparação pareada (Wilcoxon exato, Holm, bootstrap) -> analise_pareada_aceitacao.csv
python -m scripts.paired_analysis --run results/<RUN>

# 2) verificação independente das mesmas estatísticas (reimplementada, sem reutilizar o script acima)
python -m scripts.verificacao_estatistica --run results/<RUN>

# 3) figuras (PDF vetorial) e tabelas LaTeX
MPLCONFIGDIR="${TMPDIR:-/tmp}/matplotlib" python -m scripts.plots --run results/<RUN>
```

Saídas principais em `results/<RUN>/`:

| Arquivo | Conteúdo |
|---|---|
| `todos_agregados.csv` | métricas agregadas por topologia, nível, algoritmo (médias, desvios, ICs) |
| `todas_execucoes.csv` | resultados por cenário e algoritmo |
| `analise_pareada_aceitacao.csv` | as 54 comparações contra o PETIC |
| `verificacao_estatistica.csv` | resultado do verificador independente |
| `figuras/`, `tabelas/` | figuras e tabelas que entram na monografia |
| `metadados.json`, `config_usada.json` | commit, semente, configuração |

### 4.6 Chegar às conclusões da monografia (o que olhar)

1. **Aceitação.** Em `analise_pareada_aceitacao.csv`, filtre `wilcoxon_holm < 0,05`. Devem aparecer só **3 linhas**, todas do SA contra o PETIC: GÉANT l5 (p-Holm ≈ 1,8e-4), GÉANT l6 (≈ 1,2e-6) e Nobel-Germany l6 (≈ 0,017). Nas demais 51 comparações não se rejeita a hipótese nula (o que **não** prova equivalência).
2. **Confirmação independente.** `verificacao_estatistica.py` deve reproduzir as mesmas médias e valores de p, sem divergência de decisão após Holm.
3. **Equilíbrio e rotas (descritivo).** Em `todos_agregados.csv`, compare o índice de Jain e o número médio de saltos nos níveis l5 e l6: o SA tem Jain mais alto e caminhos mais longos (≈ 3,1 a 3,2 saltos contra ≈ 2,3 a 2,8 dos demais), acompanhados de menor aceitação sob congestionamento severo. A monografia apresenta isso como **associação**, sem afirmar causalidade.
4. **Tempo (descritivo).** O PETIC tem a menor média de tempo de CPU nas 18 células (conclusão da monografia). Confira nas colunas de tempo de `todos_agregados.csv` qual é o mais lento.
5. **Hipóteses.** H1 (aceitação entre PETIC, ACO e Q-Learning): resultados compatíveis, hipótese não refutada. H2 (equilíbrio/rotas do SA) e H3 (tempo) são descritivas.

Fecha-se assim a leitura da monografia: nenhuma implementação domina as outras em aceitação nos cenários avaliados, exceto o SA, que perde aceitação sob carga alta em troca de maior equilíbrio de utilização; e o PETIC entrega o menor custo computacional.

### 4.7 Compilar a monografia (opcional)

Na pasta `Projeto_de_TCC_Monografia/`:

```bash
pdflatex monografia && bibtex monografia && pdflatex monografia && pdflatex monografia
```

Exige TeX Live ou MacTeX com `abntex2`. Os números do texto trazem um comentário `% fonte:` indicando o CSV de origem.

---

## 5. Calibração (como os parâmetros foram escolhidos)

Os scripts estão em `scripts/calibracao/` e as saídas em `results/calibracao/`:

- **ACO:** variou-se número de formigas e iterações; manteve-se 10 × 20.
- **SA:** o resfriamento foi ajustado para que o orçamento de 100 iterações seja o efetivo (item 2.3).
- **Q-Learning:** varredura de episódios, taxa de aprendizado e decaimento de ε; relatório em `results/calibracao/relatorio_qlearning.md`.
- **Regressão de decisões:** `regressao_decisoes.py` (com `regressao_antes.json`) serve para conferir que otimizações de desempenho, como a lista de adjacência, não alteraram as decisões dos algoritmos.

O ACO e o SA **não foram recalibrados** depois da matriz de 30 cenários; isso é limitação declarada e trabalho futuro.

---

## 6. Limitações a lembrar ao apresentar

- Demandas **sintéticas** e apenas **três topologias** adaptadas (capacidade uniforme de 800 Mbps); não há generalização para tráfego real.
- Inferência formal **só para aceitação**; os outros resultados são descritivos.
- Os testes cujas diferenças são todas zero (ex.: níveis l1 e l2, em que todos aceitam 100%) diluem a família de 54 comparações.
- Tempo medido em CPU, **sem garantia de máquina ociosa**, com ordem fixa de execução dos algoritmos.
- A capacidade é contabilizada por período de forma independente (simplificação do conceito de elasticidade e de reuso).
- Origem exata de Abilene e GÉANT (SNDlib) e data de acesso: **[confirmar]** (pendência do autor).
- Germany50: apenas medição exploratória de tempo.

---

## 7. Mapa de arquivos

| Pasta ou arquivo | Função |
|---|---|
| `algorithms/{petic,aco,sa,q_learning}/` | os quatro alocadores |
| `domain/`, `contracts/`, `services/` | grafo, enlaces, requisições e interface comum |
| `experiments/scenarios.py` | gerador de cenários pareados |
| `experiments/run_all.py`, `runner.py` | execução da matriz |
| `metrics/` | cálculo, agregação, intervalos e exportação |
| `scripts/paired_analysis.py` | testes pareados |
| `scripts/verificacao_estatistica.py` | verificação independente |
| `scripts/plots.py` | figuras e tabelas |
| `scripts/calibracao/` | varreduras de parâmetros |
| `tests/` | suíte de testes |
| `results/` | execuções e calibrações |
