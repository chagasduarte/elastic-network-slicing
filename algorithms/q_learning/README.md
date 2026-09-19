# Q-learning para alocação de fatias

Esta implementação resolve a mesma decisão de roteamento dos demais alocadores: encontrar um caminho entre os extremos de uma requisição, com banda suficiente em todos os enlaces para a demanda do período. Usa a biblioteca padrão do Python e implementa `SliceAllocator`.

## Relação com PETIC, ACO e SA

| Implementação existente | Característica aproveitada na adaptação |
| --- | --- |
| PETIC | Filtragem por capacidade disponível no período e custo exponencial da razão entre demanda e disponibilidade. |
| ACO | Busca estocástica por caminhos, com orçamento de treinamento e registro da melhor solução completa encontrada. |
| SA | Consideração do caminho anterior para reduzir mudanças na rota. |

Os algoritmos existentes não têm uma única função objetivo comum. O PETIC também favorece fortemente a reutilização de enlaces em certas condições; o ACO ignora o período anterior; o SA combina saltos, utilização média, gargalo e distância de Jaccard entre os caminhos.

Aqui, o custo exponencial do PETIC/ACO é acrescido de uma penalidade por enlace novo. Essa escolha torna o custo aditivo e permite aprender usando somente o nó atual como estado. Ela incorpora continuidade da rota, mas não reproduz o custo completo do SA.

## Entradas e saída

```python
from algorithms.q_learning.q_learning_allocator import QLearningAllocator
from algorithms.q_learning.q_learning_config import QLearningConfig

allocator = QLearningAllocator(config=QLearningConfig(), seed=42)
result = allocator.allocate(
    graph=graph,
    request=request,
    demand=demand,
    previous_result=previous_result,
)
```

Os objetos `graph`, `request`, `demand` e `previous_result` são os mesmos usados pelos outros algoritmos; `previous_result` pode ser omitido. Não são necessários dados de treinamento externos.

`SliceResult` retorna `accepted=True`, o caminho como nomes de nós e a banda solicitada quando encontra uma rota. Na rejeição, retorna `accepted=False`, `path=[]` e `bandwidth=0`, preservando `request_id` e `demand_id`.

O alocador não modifica as reservas. Depois da aceitação, o chamador deve usar `BandwidthReservationService`, como já ocorre em [main.py](../../main.py). Origem e destino iguais produzem um caminho unitário, sem enlaces a reservar; extremos ausentes do grafo causam `ValueError`.

## Formulação

Durante uma chamada a `allocate`, ficam fixos a topologia, o destino, a banda solicitada, a ocupação do período e o caminho anterior. A tabela Q é reiniciada na próxima chamada para não misturar esses contextos.

- **Estado `s`:** nome do nó atual.
- **Ação `a`:** escolher um vizinho com enlace capaz de atender à demanda.
- **Transição:** mover-se para esse vizinho.
- **Estado terminal:** destino da requisição, sem ações futuras.
- **Recompensa:** negativo do custo do enlace escolhido.

Para banda solicitada `b` e disponibilidade `d(e)` no enlace `e`:

```text
c(e) = exp(b / d(e)) + lambda * novo(e)
r(s, a) = -c(e)
```

A ação só existe se `d(e) >= b`. A disponibilidade vem de `available_bandwidth_at(demand.id)`, incluindo reservas de outras requisições no mesmo período e desconsiderando as dos demais períodos.

`lambda` é `path_change_penalty`. `novo(e)` vale `1` se existe um caminho anterior aplicável e o enlace não pertence a ele; nos outros casos, vale `0`. O resultado anterior só é aplicável quando foi aceito, tem o mesmo `request_id` e conecta os mesmos extremos. Enlaces são comparados sem orientação. A preferência pela rota anterior continua sujeita à capacidade atual, inclusive quando a demanda aumenta.

Cada transição aplica a atualização tabular:

```text
Q(s, a) <- Q(s, a) + alpha * [r + gamma * max Q(s', a') - Q(s, a)]
```

No destino, o termo futuro é zero. Essa é a regra de Q-learning descrita por [Watkins e Dayan (1992)](https://www.gatsby.ucl.ac.uk/~dayan/papers/cjch.pdf). O custo e a representação do ambiente acima são escolhas desta adaptação.

Com `discount_factor=1.0`, maximizar o retorno equivale a minimizar a soma dos custos dos enlaces. Com `path_change_penalty=0.0`, essa soma corresponde à usada pelo ACO e pelo cálculo normal de pesos do PETIC.

## Treinamento e construção da rota

1. Construir as ações viáveis e seus custos a partir da ocupação atual.
2. Verificar se origem e destino pertencem à mesma componente viável. Essa verificação não constrói uma rota.
3. Inicializar os valores Q em zero e executar os episódios a partir da origem.
4. Escolher uma ação aleatória com probabilidade `epsilon`; caso contrário, escolher uma de maior Q, com desempate aleatório.
5. Atualizar Q a cada transição e reduzir `epsilon` a cada episódio até `epsilon_min`.
6. Guardar a melhor rota simples obtida dos episódios que chegaram ao destino.
7. Extrair também a rota gulosa da tabela final e compará-la com a melhor rota guardada.

O treinamento permite revisitar nós. Proibir revisitas faria as ações dependerem do histórico do percurso, que não está representado no estado por nó. Cada episódio tem um limite de passos; atingir esse limite interrompe a coleta, mas preserva o bootstrap da última atualização. Apenas alcançar o destino zera o valor futuro.

Os ciclos são removidos das trajetórias completas antes de compará-las. Na extração gulosa, uma repetição invalida aquela candidata. O caminho retornado sempre é simples. A comparação considera `sum(gamma ** passo * custo)`, com o primeiro passo em zero; não há uma rota alternativa fornecida por Dijkstra.

A propriedade `allocator.q_table` fornece uma cópia dos valores da última alocação para inspeção. O destino tem um dicionário de ações vazio. A semente controla um gerador local que avança durante a sequência de chamadas; instâncias novas com a mesma semente e a mesma sequência de entradas reproduzem o experimento.

## Parâmetros e limites

Os parâmetros estão em [QLearningConfig](q_learning_config.py), com seus padrões e exemplos também no [README principal](../../README.md). `max_steps_per_episode=None` usa `4 * número_de_nós` passos; os episódios padrão são `2000`.

O orçamento é finito: a implementação não garante convergência nem rota ótima, e pode rejeitar um caminho viável quando a busca não o encontra dentro dos limites. A tabela Q não persiste entre demandas ou processos; a informação temporal usada entre períodos é `previous_result`.

Para comparar o custo total com PETIC/ACO, mantenha `discount_factor=1.0`. Valores menores mudam o objetivo: descontar custos futuros pode favorecer atrasar a chegada por ciclos, e remover esses ciclos pode aumentar o custo descontado. A saída ainda é restrita a caminhos simples, mas nesse modo o objetivo aprendido e essa restrição podem divergir.

O modelo de saída identifica enlaces pelos seus extremos. Se houver enlaces paralelos, o alocador considera o primeiro do par, acompanhando o comportamento de `NetworkGraph.get_link` usado na reserva.

## Executar e validar

Na raiz do projeto:

```bash
python3 main.py --algorithm q-learning --seed 42
python3 -m unittest discover -s tests -v
```

O cenário padrão usa Germany50, origem `A`, destino `L` e demandas `40`, `50`, `15` e `320` Mbps em períodos distintos. Os testes verificam capacidade, reservas externas, mudanças de contexto, uso da rota anterior, atualização Q e o mesmo cenário de quatro períodos.
