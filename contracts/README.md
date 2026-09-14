# Topologias padronizadas

Estas versões usam identificadores simples para os nós:

- Abilene: A até L
- Nobel-Germany: A até Q
- GEANT: A até V
- Germany50: A até Z e AA até AX

`NODE_LOCATIONS` continua indicando a localização real associada a cada letra.
`ORIGINAL_NODE_NAMES` preserva o nome original da instância SNDlib para
rastreabilidade acadêmica.

Assim, a lógica da `main.py` pode continuar trabalhando com `Node("A")`,
`Node("B")`, `Node("L")`, etc., sem depender dos nomes originais das redes.

Observação: em topologias com mais de 26 nós, após Z são usados AA, AB, AC...
