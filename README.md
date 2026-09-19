# Elastic Network Slicing

Simulador em Python para estudar a alocação de fatias de rede com demandas de largura de banda que variam ao longo de períodos. Desenvolvido no contexto de um TCC, o projeto reúne implementações de PETIC, Ant Colony Optimization (ACO) e Simulated Annealing (SA) sobre topologias representadas por grafos.

Cada requisição conecta uma origem a um destino e define a banda necessária em cada período. O simulador busca um caminho com capacidade disponível, registra a reserva nos enlaces e passa o resultado ao próximo período, permitindo que o algoritmo considere a alocação anterior.

## Requisitos e execução

- Python **3.10 ou superior**, por causa das anotações de tipo usadas no código.
- Apenas a biblioteca padrão do Python; não há dependências externas para instalar.

Na raiz do repositório, execute:

```bash
python3 main.py
```

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

A topologia, a requisição e o algoritmo são configurados diretamente em [main.py](main.py).

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

Mantenha apenas um bloco de criação de `allocator` ativo em `main.py`. Os imports usados nos exemplos abaixo já estão presentes nesse arquivo.

| Algoritmo | Comportamento implementado | Uso do período anterior |
| --- | --- | --- |
| PETIC | Usa Dijkstra com custo exponencial da razão entre banda solicitada e banda disponível. Descarta enlaces sem capacidade. | Favorece enlaces do caminho anterior quando a demanda atual não supera a banda anteriormente aceita. |
| ACO | Constrói caminhos probabilísticos com feromônios e uma heurística de disponibilidade de banda, aplicando evaporação e reforço a cada iteração. | Recebe `previous_result`, mas não o utiliza; os feromônios são reiniciados a cada alocação. |
| SA | Parte de um caminho viável obtido por Dijkstra e explora caminhos vizinhos com resfriamento e aceitação probabilística de soluções de maior custo. | Inclui no custo a diferença entre os enlaces do caminho atual e do anterior. |

#### PETIC

Esta é a configuração já ativa:

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

Substitua o bloco de construção do PETIC por:

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

Substitua o bloco de construção do PETIC pelo exemplo abaixo. Mova a inicialização de `reservation_service` para este ponto e remova sua inicialização posterior em `main.py`, mantendo a chamada de reserva dentro do laço de demandas.

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

O bloco de SA originalmente comentado em `main.py` usa `reservation_service` antes de sua criação; por isso, ativá-lo exige o ajuste de ordem mostrado acima. Há também uma limitação no tratamento de demandas inviáveis, descrita abaixo.

## Estrutura do projeto

```text
elastic-network-slicing/
├── main.py                     # Configuração e execução dos períodos
├── algorithms/
│   ├── petic/                  # Alocador PETIC e cálculo de pesos
│   ├── aco/                    # Alocador por colônia de formigas
│   └── sa/                     # Alocador, custo, vizinhança e configuração do SA
├── contracts/                  # Interfaces abstratas e construção de topologias
├── domain/                     # Nós, enlaces, requisições, demandas e resultados
├── pathfinding/                # Implementação de Dijkstra
├── services/                   # Validação e reserva de largura de banda
└── metrics/                    # Arquivos reservados para futuras métricas
```

A interface [SliceAllocator](contracts/slice_allocator.py) define o método `allocate(graph, request, demand, previous_result=None)`. Novos alocadores podem implementar esse contrato e ser instanciados em `main.py`, preservando o fluxo de reserva por período.

## Estado atual e limitações

- O programa executa uma requisição com vários períodos. Experimentos com várias requisições exigem adaptar o fluxo de `main.py` e compartilhar o grafo entre elas.
- Os arquivos `allocation_success_rate.py`, `computational_cost.py` e `link_saturation.py`, em `metrics/`, estão vazios. Essas métricas ainda não são calculadas nem exportadas.
- Não há suíte de testes automatizados no repositório. A execução padrão foi verificada com Python 3.14.7, com aceitação dos quatro períodos.
- No SA, a rejeição por ausência de caminho viável chama `SliceResult` com `period_id`, mas o modelo espera `demand_id`. Esse caso gera `TypeError` e precisa ser corrigido antes de usar o SA em experimentos com rejeições.

Para comparar algoritmos, recrie o grafo a cada execução independente, use as mesmas demandas e capacidades e registre os parâmetros e sementes utilizados.
