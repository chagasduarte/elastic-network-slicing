# Topologias SNDlib adaptadas para o simulador do TCC

Arquivos:
- `abilene_topology.py` — 12 nós, 15 enlaces.
- `nobel_germany_topology.py` — 17 nós, 26 enlaces.
- `geant_topology.py` — 22 nós, 36 enlaces.
- `germany50_topology.py` — 50 nós, 88 enlaces.

Com a topologia de Fortaleza que já existe no projeto, isso fornece cinco
topologias para a bateria experimental.

## Importante sobre as capacidades

A classe `Link` do simulador recebe uma capacidade fixa, porém algumas
instâncias SNDlib são problemas de projeto de rede: a capacidade
pré-instalada pode ser zero e o arquivo fornece módulos/opções de capacidade
que poderiam ser instalados.

Por isso:

### Abilene
Foram preservadas as capacidades pré-instaladas da instância SNDlib
(9920 Mbit/s na maioria dos enlaces e 2480 Mbit/s em ATLAng-IPLSng).

### GEANT
O arquivo SNDlib fornece capacidade pré-instalada 0 e um módulo adicional
de 40000 Mbit/s em cada enlace. A adaptação materializa um módulo por enlace
por padrão. O parâmetro `link_capacity` permite alterar o cenário.

### Nobel-Germany
O arquivo SNDlib fornece capacidade pré-instalada 0 e uma lista de opções
de capacidade. Como o simulador exige uma capacidade fixa, foi usado
800 Mbit/s por padrão, correspondente ao maior valor listado nas opções.
O parâmetro `link_capacity` permite definir outro cenário.

### Germany50
O arquivo SNDlib fornece capacidade pré-instalada 0 e um módulo adicional
de 40 Mbit/s. A função recebe `modules_per_link`; por padrão usa 20 módulos,
ou 800 Mbit/s por enlace:

    capacidade = 40 * modules_per_link

Esse número de módulos é uma decisão experimental e deve ser documentado
como tal no TCC.

## Recomendação metodológica

Para comparar PETIC, ACO e SA, mantenha exatamente a mesma topologia,
capacidades, sequência de demandas e semente aleatória para todos os
algoritmos. Se desejar comparar redes com escalas de capacidade diferentes,
normalize a carga oferecida em relação à capacidade total ou residual, em
vez de usar a mesma demanda absoluta em todas as topologias.

## Fontes
SNDlib — Survivable Network Design Library:
https://sndlib.put.poznan.pl/

As conectividades e coordenadas destes arquivos foram transcritas das
instâncias públicas correspondentes da SNDlib.
