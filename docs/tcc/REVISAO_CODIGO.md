# Revisão do código — elastic-network-slicing

Foco: corretude dos algoritmos, métricas e experimentos. Revisei todo o código, exceto os arquivos de topologia e os testes, que li por amostragem. Os 115 testes passam (1 falha esperada, no ACO). Rodei `experiments.cli` nas topologias `test` e `germany50`.

---

## 🔴 Crítico — invalida a comparação se não for resolvido

### 1. Com uma única requisição, nenhum algoritmo é colocado sob pressão

`experiments/cli.py` cria **uma** `SliceRequest`. Como a capacidade é contabilizada por período (`Link.available_bandwidth_at(demand_id)`), cada período começa com a rede **vazia**. Resultado medido:

| Topologia | Aceitação (todos os algoritmos) | Utilização média |
|---|---|---|
| test | 100% | 7–10% |
| germany50 | 100% | **0,9%** |

Com isso, aceitação, banda atendida, saturação e Jain não diferenciam os algoritmos. A pergunta do TCC ("em quais cenários cada abordagem é melhor") não pode ser respondida.

**O que fazer:**

- Gerar **N requisições simultâneas** por cenário, com pares origem/destino sorteados por semente fixa. O `ExperimentRunner` já suporta várias requisições: só o CLI não as cria.
- Criar **níveis de carga** (por exemplo, N = 10, 20, 40, 80, ou um multiplicador sobre as demandas) até chegar perto da saturação.
- Gerar as demandas por período com um **perfil diário** (baixa → pico → baixa) multiplicado por ruído individual. É isso que caracteriza a "demanda elástica" do texto.

### 2. As capacidades das topologias não são comparáveis

Abilene usa 9.920 Mbps, GÉANT usa 40.000 Mbps, e Nobel-Germany e Germany50 usam 800 Mbps. Com demandas de dezenas de Mbps, Abilene e GÉANT nunca saturam. **Use a mesma capacidade em todas** (ex.: `create_geant_graph(link_capacity=800)`, `create_abilene_graph(capacity_scale=800/9920)`) ou faça a carga escalar com a capacidade.

---

## 🟠 Importante — afeta a corretude ou o texto do TCC

### 3. O Q-Learning implementado não é o descrito na Fundamentação (p. 15–16)

- **Texto:** o estado é a "disponibilidade residual de enlaces e nós", e as ações são "decisões de alocação e escalonamento".
- **Código:** o estado é o **nó atual**, a ação é o **próximo vizinho**, e a tabela Q é **reiniciada a cada demanda**.

Na prática, o código usa o Q-Learning como um *buscador de caminho* treinado do zero em cada alocação, sem aprender nada entre períodos. É uma escolha válida, mas o texto precisa refletir isso (a Metodologia que escrevi já descreve o que o código faz). Ajuste o último parágrafo da seção 2.6.4 ou mencione essa limitação na discussão.

### 4. A condição de reutilização do PETIC pode divergir do artigo

```python
can_reuse_previous_slice = (... and previous_result.bandwidth >= demand.bandwidth)
```

O enlace antigo só ganha peso ε quando a demanda **não aumentou**. O texto (p. 12) diz: "caso os recursos dessa fatia **ainda sejam capazes de atender à nova demanda**". Como a capacidade é recalculada por período e `link.supports()` já é verificado antes, uma leitura mais fiel seria reaproveitar sempre que os enlaces anteriores suportarem a nova banda, mesmo que ela tenha aumentado. **Confira em Gomes et al. (2018)** qual é a regra e alinhe o código e o texto.

### 5. O ACO ignora o período anterior

`AcoAllocator.allocate` recebe `previous_result`, mas não o usa. O PETIC, o SA e o Q-Learning favorecem a continuidade, e o ACO não. Isso vai aparecer como uma **taxa de reutilização menor no ACO**, e é preciso dizer no texto que isso vem do desenho, e não da meta-heurística em si. Uma opção simples, se quiser equilibrar: inicializar com mais feromônio os enlaces do caminho anterior.

### 6. Os defaults do ACO no README não batem com o código

O README diz `ants_count=20, iterations=50, beta=2.0`. O código (que é o que roda, via `inspect.signature`) usa **10, 20 e 1.0**. Na Metodologia usei os valores do código. Corrija o README ou mude os defaults, mas mantenha os dois iguais.

### 7. O SA roda só 108 iterações

Com `T0=0.25`, `Tmin=0.001` e `λ=0.95`, a temperatura cai abaixo do mínimo na iteração 108, então `max_iterations=500` nunca é atingido. Isso não é um bug, mas o orçamento de busca do SA (108 vizinhos) fica bem menor que o do ACO (200 formigas) e o do Q-Learning (2.000 episódios). Registre isso, ou calibre os parâmetros para orçamentos comparáveis.

Além disso, o SA **parte do caminho de menor número de saltos (Dijkstra)**, ou seja, já começa de uma boa solução. Vale citar isso no texto.

### 8. Cada algoritmo otimiza uma função objetivo diferente

O PETIC, o ACO e o Q-Learning usam `exp(b/a)`. O SA usa saltos, utilização média, gargalo e Jaccard. Isso é legítimo, mas por isso a comparação **precisa** ser feita pelas métricas comuns (aceitação, utilização, Jain, saltos, reutilização, tempo), e não pelo custo interno de cada algoritmo. O módulo de métricas já faz isso corretamente.

---

## 🟡 Métricas e estatística

9. **Desvio-padrão populacional (`pstdev`)**: para amostras de repetições, use o **amostral** (`statistics.stdev`) e reporte o **intervalo de confiança de 95%** (`média ± t·s/√n`). Com 5 repetições o IC fica largo, então use pelo menos 10, ou idealmente 30, para os algoritmos estocásticos.
10. **Enlaces saturados** só contam quando `used >= capacity` (100%). Considere também um limiar, por exemplo ≥ 80% ou ≥ 90%, que mostra melhor quem "espreme" a rede.
11. **O índice de Jain no resumo geral** mistura todos os pares enlace × período. Para o texto, prefira o Jain **por período** (já calculado em `periods`) e a média entre os períodos.
12. **O tempo de decisão** reflete a implementação: `get_neighbors` e `get_link` percorrem a lista inteira de enlaces (O(|E|)), e o SA levou 7–19 s para 4 demandas no Germany50. Isso vale igualmente para todos os algoritmos, então a comparação relativa se mantém, mas um dicionário de adjacência reduziria muito o tempo dos experimentos maiores.
13. `metrics/allocation_success_rate.py`, `computational_cost.py` e `link_saturation.py` estão **vazios**, e a seção do README sobre métricas está desatualizada. Apague os arquivos e atualize o README.

---

## ⚪ Menores

- No SA, `_rejected_result` devolve `bandwidth=demand.bandwidth` com `accepted=False`, enquanto os outros alocadores devolvem `0`. Não afeta as métricas (o coletor ignora), mas deixe consistente.
- O README diz que o SA dá `TypeError` em rejeições, mas isso já foi corrigido (o código usa `demand_id`). Remova o aviso.
- O SA recebe `reservation_service` e não usa. Pode remover.
- `NetworkGraph.get_links()` tem um `;` e é redundante com a propriedade `links`.
- `PeticWeightCalculator.calculate` tem a assinatura `(link, demand: SliceDemand)`, mas o contrato `LinkWeightCalculator` declara `bandwidth: int`.
- O teste `expectedFailure` do ACO (origem = destino divide por zero) é um bug real, que vai aparecer se o sorteio de pares gerar origem igual ao destino. Ou corrija, ou garanta que o gerador de requisições nunca sorteie origem = destino.

---

## Ordem sugerida

1. Itens 1 e 2: gerador de cenários com várias requisições, carga crescente e capacidade uniforme. **Sem isso não há resultados.**
2. Item 4: conferir a regra do PETIC no artigo.
3. Item 9: desvio amostral, IC e mais repetições.
4. Itens 3, 5, 6 e 7: ajustar o texto ou o código para ficarem coerentes.
5. O resto, quando der.
