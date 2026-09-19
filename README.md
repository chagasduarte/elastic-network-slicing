# Elastic Network Slicing

Simulador em Python para estudar a alocação de fatias de rede com demandas de largura de banda que variam ao longo de períodos. Desenvolvido no contexto de um TCC, o projeto reúne implementações de PETIC, Ant Colony Optimization (ACO), Simulated Annealing (SA) e Q-learning sobre topologias representadas por grafos.

Cada requisição conecta uma origem a um destino e define a banda necessária em cada período. O simulador busca um caminho com capacidade disponível, registra a reserva nos enlaces e passa o resultado ao próximo período, permitindo que o algoritmo considere a alocação anterior.

## Requisitos e execução

- Python **3.10 ou superior**, por causa das anotações de tipo usadas no código.
- Apenas a biblioteca padrão do Python; não há dependências externas para instalar.

Na raiz do repositório, execute:

```bash
python3 main.py
```

Para selecionar outro algoritmo e definir a semente:

```bash
python3 main.py --algorithm petic
python3 main.py --algorithm aco --seed 42
python3 main.py --algorithm sa --seed 42
python3 main.py --algorithm q-learning --seed 42
python3 main.py --help
```

O padrão continua sendo PETIC; a semente padrão é `42`. A semente controla os geradores locais de ACO, SA e Q-learning e não altera o PETIC, que é determinístico.

Opcionalmente, crie um ambiente virtual antes de executar:

```bash
python3 -m venv .venv
source .venv/bin/activate
python main.py
```

No Windows com PowerShell, a ativação é feita com `.venv\Scripts\Activate.ps1`.

### Cenário padrão

A configuração atual de [main.py](main.py) usa:

| Parâmetro | Valor |
| --- | --- |
| Topologia | Germany50: 50 nós e 88 enlaces |
| Capacidade de cada enlace | 800 Mbps |
| Algoritmo | PETIC com Dijkstra |
| Requisição | `request-1`, de `A` até `L` |
| Demandas por período | `t1`: 40, `t2`: 50, `t3`: 15 e `t4`: 320 Mbps |

Nesse cenário, os quatro períodos são aceitos. Trecho da saída:

```text
Request: request-1
Demanda: t1
Bandwidth: 40 Mbps
Caminho: A -> AW -> O -> K -> Z -> N -> L
========================================
```

Os períodos seguintes exibem seus respectivos valores de banda e, nessa configuração, mantêm o mesmo caminho. Os resultados são impressos no terminal; as reservas ficam em memória durante a execução.

## Modelo e fluxo de alocação

| Componente | Responsabilidade |
| --- | --- |
| `Node` | Identifica um nó pelo atributo `name`. |
| `Link` | Representa um enlace com capacidade e reservas por período. |
| `NetworkGraph` | Mantém os nós, enlaces e consultas de vizinhança e caminhos. |
| `SliceRequest` | Define a origem, o destino e a lista de demandas de uma requisição. |
| `SliceDemand` | Define o identificador do período e a banda solicitada. |
| `SliceResult` | Informa aceitação, caminho, banda e identificadores da decisão. |
| `LinkAllocation` | Registra a banda reservada para uma requisição em um período. |

Os enlaces são tratados como **não direcionados**, com a mesma capacidade compartilhada entre os dois sentidos. Capacidades e demandas são expressas em Mbps nos cenários do projeto.

Para cada demanda, o fluxo de `main.py` é:

1. Chamar `allocator.allocate(...)`, passando também `previous_result`.
2. Exibir o caminho aceito e a banda solicitada, ou a mensagem de rejeição.
3. Se a demanda for aceita, converter o caminho em enlaces, criar uma `LinkAllocation` e reservar a banda com `BandwidthReservationService`.
4. Guardar o resultado para a próxima demanda.

**A escolha do caminho e a reserva são etapas separadas.** Os alocadores retornam um `SliceResult`; a chamada ao serviço de reserva é feita por `main.py`. O serviço valida a capacidade de todos os enlaces do caminho antes de registrar a alocação.

A ocupação é calculada por `demand_id`: reservas de `t1` não consomem a capacidade disponível em `t2`. Ao simular várias requisições concorrentes, use o mesmo identificador para demandas que pertencem ao mesmo período. A ordem dos períodos é a ordem da lista `request.demands`.

## Configuração dos experimentos

A topologia e a requisição são configuradas em [main.py](main.py). O algoritmo é selecionado por `--algorithm`; os parâmetros específicos de cada alocador podem ser alterados na função `create_allocator`.

### Alterar origem, destino e demandas

Edite a construção de `SliceRequest`, por exemplo:

```python
request = SliceRequest(
    id="request-1",
    source=Node("A"),
    destination=Node("L"),
    demands=[
        SliceDemand(id="t1", bandwidth=40),
        SliceDemand(id="t2", bandwidth=80),
        SliceDemand(id="t3", bandwidth=20),
    ],
)
```

Os nós escolhidos devem existir na topologia. As demandas precisam ter identificador não vazio e banda maior que zero.

### Escolher uma topologia

As contagens e capacidades abaixo correspondem às implementações presentes no repositório, usando os parâmetros padrão.

| Topologia | Nós | Enlaces | Capacidade por enlace (Mbps) | Função de criação |
| --- | ---: | ---: | --- | --- |
| Teste sintético | 12 | 23 | 40 a 320 | [`create_test_graph()`](contracts/create_topo.py) |
| Fortaleza experimental | 12 | 23 | 40 a 320 | [`create_test_graph_fortal()`](contracts/create_topo.py) |
| Abilene | 12 | 15 | 14 enlaces de 9920 e 1 de 2480 | [`create_abilene_graph(capacity_scale=1.0)`](contracts/abilene_topology.py) |
| Nobel-Germany | 17 | 26 | 800 | [`create_nobel_germany_graph(link_capacity=800)`](contracts/nobel_germany_topology.py) |
| GEANT | 22 | 36 | 40000 | [`create_geant_graph(link_capacity=40000)`](contracts/geant_topology.py) |
| Germany50 | 50 | 88 | 800 | [`create_germany50_graph(modules_per_link=20)`](contracts/germany50_topology.py) |

Para usar GEANT com capacidades de 800 Mbps, por exemplo, substitua a criação de `graph` e use o import correspondente:

```python
from contracts.geant_topology import create_geant_graph

graph = create_geant_graph(link_capacity=800)
```

Nos módulos Abilene, Nobel-Germany, GEANT e Germany50, os dicionários `NODE_LOCATIONS`, `ORIGINAL_NODE_NAMES` e `NODE_COORDINATES` associam os identificadores às localidades, aos nomes de origem e às coordenadas. A Germany50 usa identificadores de `A` a `Z` e de `AA` a `AX`. Consulte também [a documentação das topologias](contracts/README.md).

Os comentários desses módulos descrevem a conectividade como transcrita de instâncias da SNDlib. As capacidades incluem adaptações para os experimentos: na Germany50, cada enlace recebe `40 * modules_per_link` Mbps, resultando em 800 Mbps por padrão. Esse valor é uma escolha do simulador. Em Fortaleza, os locais representam pontos reais, enquanto as conexões e capacidades são experimentais.

### Escolher um algoritmo

Use a opção `--algorithm` ou chame `main(algorithm="q-learning", seed=42)` em Python. A chamada `main()` mantém a execução padrão. A função `create_allocator` centraliza a construção dos quatro alocadores; os exemplos abaixo mostram como personalizar seus parâmetros.

| Algoritmo | Comportamento implementado | Uso do período anterior |
| --- | --- | --- |
| PETIC | Usa Dijkstra com custo exponencial da razão entre banda solicitada e banda disponível. Descarta enlaces sem capacidade. | Favorece enlaces do caminho anterior quando a demanda atual não supera a banda anteriormente aceita. |
| ACO | Constrói caminhos probabilísticos com feromônios e uma heurística de disponibilidade de banda, aplicando evaporação e reforço a cada iteração. | Recebe `previous_result`, mas não o utiliza; os feromônios são reiniciados a cada alocação. |
| SA | Parte de um caminho viável obtido por Dijkstra e explora caminhos vizinhos com resfriamento e aceitação probabilística de soluções de maior custo. | Inclui no custo a diferença entre os enlaces do caminho atual e do anterior. |
| Q-learning | Aprende valores de ações entre nós com exploração epsilon-greedy e recompensa negativa do custo dos enlaces viáveis. Retorna o melhor caminho completo encontrado, comparando os episódios com a política gulosa. | Penaliza enlaces novos em relação ao caminho anterior aceito da mesma requisição e dos mesmos extremos. A tabela Q é reiniciada a cada alocação. |

#### PETIC

Configuração usada por `--algorithm petic`:

```python
path_finder = DijkstraPathFinder()
weight_calculator = PeticWeightCalculator()

allocator = PeticAllocator(
    path_finder=path_finder,
    weight_calculator=weight_calculator,
)
```

O peso normal de um enlace é `exp(banda_solicitada / banda_disponivel)`. Quando a reutilização é aplicável, os enlaces viáveis do caminho anterior recebem peso `0.0001`, favorecendo sua permanência na rota.

#### Ant Colony Optimization (ACO)

Configuração usada por `--algorithm aco` com a semente padrão:

```python
allocator = AcoAllocator(
    ants_count=20,
    iterations=50,
    alpha=1.0,
    beta=2.0,
    evaporation_rate=0.1,
    initial_pheromone=1.0,
    pheromone_deposit=1.0,
    seed=42,
)
```

`ants_count` e `iterations` controlam o esforço de busca; `alpha` e `beta` controlam a influência dos feromônios e da heurística. A semente fixa ajuda a repetir os experimentos. Por padrão, o construtor usa `seed=None`.

#### Simulated Annealing (SA)

Configuração usada por `--algorithm sa`. O serviço de reserva é criado antes do alocador e a reserva continua sendo feita no laço de demandas:

```python
reservation_service = BandwidthReservationService()
config = SimulatedAnnealingConfig()
random_generator = random.Random(42)

allocator = SimulatedAnnealingAllocator(
    path_finder=DijkstraPathFinder(),
    cost_calculator=SimulatedAnnealingCostCalculator(config),
    neighbor_generator=SimulatedAnnealingNeighborGenerator(
        config=config,
        random_generator=random_generator,
    ),
    reservation_service=reservation_service,
    config=config,
    random_generator=random_generator,
)
```

[SimulatedAnnealingConfig](algorithms/sa/simulated_annealing_config.py) define temperatura inicial `0.25`, temperatura mínima `0.001`, fator de resfriamento `0.95` e limite de 500 iterações. O custo combina quantidade normalizada de saltos, utilização média, utilização do enlace mais ocupado e mudança de caminho, com pesos `0.20`, `0.30`, `0.35` e `0.15`, respectivamente. As utilizações são projetadas considerando a inclusão da demanda atual. Ao alterar os pesos, a soma deve continuar igual a `1.0`.

Há uma limitação existente no tratamento de demandas inviáveis do SA, descrita abaixo.

#### Q-learning

O Q-learning recebe exatamente o contrato dos demais alocadores:

```python
result = allocator.allocate(
    graph=graph,
    request=request,
    demand=demand,
    previous_result=previous_result,
)
```

`graph` fornece nós, enlaces e capacidade disponível no período; `request` fornece os identificadores, a origem e o destino; `demand` fornece o período e a banda exigida. `previous_result` é opcional e permite favorecer a continuidade do caminho. O retorno é o mesmo `SliceResult` usado pelos outros algoritmos. O treinamento não reserva banda nem altera o grafo.

Configuração usada por `--algorithm q-learning`:

```python
allocator = QLearningAllocator(
    config=QLearningConfig(
        episodes=2000,
        learning_rate=0.2,
        discount_factor=1.0,
        epsilon_start=1.0,
        epsilon_min=0.05,
        epsilon_decay=0.995,
        max_steps_per_episode=None,
        path_change_penalty=0.15,
    ),
    seed=42,
)
```

| Parâmetro | Padrão | Função |
| --- | ---: | --- |
| `episodes` | `2000` | Quantidade de episódios de treinamento por demanda. |
| `learning_rate` | `0.2` | Taxa de atualização dos valores Q (`alpha`). |
| `discount_factor` | `1.0` | Peso do custo futuro (`gamma`), entre `0.0` e `1.0`; com `1.0`, considera a soma dos custos do caminho. |
| `epsilon_start` | `1.0` | Probabilidade inicial de explorar uma ação aleatória. |
| `epsilon_min` | `0.05` | Limite inferior da probabilidade de exploração. |
| `epsilon_decay` | `0.995` | Fator multiplicativo de redução de epsilon a cada episódio. |
| `max_steps_per_episode` | `None` | Limita a duração do episódio; `None` usa quatro vezes o número de nós. |
| `path_change_penalty` | `0.15` | Custo adicional por enlace ausente do caminho anterior aplicável; use `0.0` para desativá-lo. |

O **estado** é o nó atual e cada **ação** escolhe um vizinho ligado por um enlace com capacidade suficiente para a demanda no período. Cada episódio começa na origem e termina ao chegar ao destino ou atingir o limite de passos. Revisitas a nós são permitidas durante o aprendizado, mantendo as ações dependentes apenas do nó no cenário fixo daquela alocação.

O custo de uma ação é `exp(banda_solicitada / banda_disponivel)` mais a penalidade de mudança, quando aplicável. A parte exponencial segue o custo usado por PETIC e ACO; a penalidade favorece continuidade, inspirada no SA. Ela é aditiva por enlace novo, **não corresponde à distância de Jaccard** entre caminhos usada no SA. Só há essa penalidade quando o resultado anterior foi aceito, pertence à mesma requisição e tem os mesmos extremos.

A recompensa é o negativo desse custo. A atualização segue:

```text
Q(s, a) <- Q(s, a) + alpha * (r + gamma * max Q(s', a') - Q(s, a))
```

No destino, o valor futuro é zero. O limite de passos é um truncamento do treinamento: atingir esse limite não transforma o nó atual em destino, e a última atualização preserva a estimativa do valor futuro.

A tabela Q é reiniciada em cada `allocate`, pois o período, a ocupação, a banda solicitada e o caminho anterior podem mudar. Ao final, o alocador compara o melhor caminho sem ciclos extraído dos episódios que chegaram ao destino com o caminho da política gulosa, e retorna o de menor custo. Essa comparação usa o mesmo `gamma` do treinamento: soma `gamma ** passo * custo_do_enlace`, com o primeiro passo em zero. Com `gamma=1.0` e penalidade de mudança igual a zero, o objetivo corresponde à soma dos custos exponenciais usada pelo ACO e pelo PETIC quando o favorecimento do caminho anterior não se aplica.

Se não encontrar caminho completo, o Q-learning rejeita a demanda. Não há busca auxiliar por Dijkstra: com um orçamento finito de exploração, o algoritmo pode rejeitar uma demanda viável e não garante o caminho ótimo.

A formulação e suas escolhas estão detalhadas em [Q-learning para alocação de fatias](algorithms/q_learning/README.md). A regra de atualização tem como referência [Watkins e Dayan (1992), *Q-learning*](https://doi.org/10.1007/BF00992698); os parâmetros e o orçamento de treinamento deste simulador não constituem uma garantia de convergência.

## Estrutura do projeto

```text
elastic-network-slicing/
├── main.py                     # Configuração e execução dos períodos
├── algorithms/
│   ├── petic/                  # Alocador PETIC e cálculo de pesos
│   ├── aco/                    # Alocador por colônia de formigas
│   ├── sa/                     # Alocador, custo, vizinhança e configuração do SA
│   └── q_learning/             # Alocador, configuração e formulação do Q-learning
├── contracts/                  # Interfaces abstratas e construção de topologias
├── domain/                     # Nós, enlaces, requisições, demandas e resultados
├── pathfinding/                # Implementação de Dijkstra
├── services/                   # Validação e reserva de largura de banda
├── tests/                      # Testes automatizados do Q-learning e integração
└── metrics/                    # Arquivos reservados para futuras métricas
```

A interface [SliceAllocator](contracts/slice_allocator.py) define o método `allocate(graph, request, demand, previous_result=None)`. Novos alocadores podem implementar esse contrato e ser instanciados em `main.py`, preservando o fluxo de reserva por período.

## Testes

Execute a suíte com a biblioteca padrão:

```bash
python3 -m unittest discover -s tests -v
```

Os testes verificam o contrato do Q-learning, capacidade por período, rejeições, influência do resultado anterior e reprodução com semente fixa. Para executar os quatro algoritmos no mesmo cenário, use os comandos da seção de execução; cada processo cria um grafo novo.

## Estado atual e limitações

- O programa executa uma requisição com vários períodos. Experimentos com várias requisições exigem adaptar o fluxo de `main.py` e compartilhar o grafo entre elas.
- Os arquivos `allocation_success_rate.py`, `computational_cost.py` e `link_saturation.py`, em `metrics/`, estão vazios. Essas métricas ainda não são calculadas nem exportadas.
- O Q-learning treina novamente a cada demanda; não há persistência da tabela Q nem aprendizado entre execuções. Os algoritmos usam objetivos distintos, por isso comparar apenas a aceitação não mede qualidade de caminho ou custo de busca.
- No SA, a rejeição por ausência de caminho viável chama `SliceResult` com `period_id`, mas o modelo espera `demand_id`. Esse caso gera `TypeError` e precisa ser corrigido antes de usar o SA em experimentos com rejeições.

Para comparar algoritmos, recrie o grafo a cada execução independente, use as mesmas demandas e capacidades e registre os parâmetros e sementes utilizados.
