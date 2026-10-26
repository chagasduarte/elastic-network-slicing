Você vai me ajudar a terminar meu TCC de Ciência da Computação (UVA, 2026), com o título "Alocação dinâmica de recursos para formação de fatias de rede em ambientes de demanda elástica". Este repositório é o simulador em Python que compara quatro alocadores: PETIC, ACO, Simulated Annealing e Q-Learning.

Antes de qualquer coisa, leia por completo:
- README.md
- docs/tcc/REVISAO_CODIGO.md: revisão do código com os problemas em ordem de prioridade
- docs/tcc/metodologia.tex: capítulo de Metodologia já escrito, com trechos marcados [PENDENTE]

OBJETIVO: montar a estrutura completa para eu sair daqui com experimentos válidos, gráficos, tabelas e o rascunho de Resultados.

COMO TRABALHAR:
- Crie a branch `tcc-estrutura` e faça um commit por fase.
- Rode `python3 -m unittest discover -s tests` antes de cada commit; os testes precisam passar.
- Ao fim de cada fase, PARE: me mostre um resumo curto do que mudou e espere meu OK para seguir.
- Nunca invente dados, números ou referências. Se faltar uma decisão, me pergunte.
- NÃO altere o comportamento de nenhum algoritmo (escolha de caminho, custos, parâmetros) sem me perguntar antes. O texto do TCC descreve esse comportamento.
- Tudo precisa ser reprodutível por semente.

FASE 0 — CLAUDE.md
Crie um CLAUDE.md na raiz com: o contexto do TCC, a arquitetura (domain/, algorithms/, contracts/, metrics/, experiments/), os comandos de teste e de experimento, as convenções (Python 3.10, núcleo só com a biblioteca padrão, nomes e mensagens em português como já estão) e as regras acima.

FASE 1 — Cenários de demanda elástica (itens 1 e 2 da revisão; sem isso não há resultados)
- Crie experiments/scenarios.py, que gera N requisições com pares origem→destino distintos sorteados por semente, nunca com origem igual ao destino.
- As demandas por período vêm de um perfil diário (ex.: madrugada baixa, manhã média, pico à noite) multiplicado por um ruído individual de cada requisição.
- Implemente níveis de carga, variando N e/ou um multiplicador das demandas, desde carga leve até perto da saturação.
- Use a mesma capacidade configurável em todos os enlaces de todas as topologias.
- Defina os cenários em JSON, em experiments/configs/, para eu editar sem mexer no código. O CLI deve aceitar --config.
- Escreva testes para o gerador (reprodutibilidade, ausência de origem = destino, formato das demandas).
- Antes de fechar, rode um cenário pequeno e me mostre que a aceitação agora DIFERE entre os algoritmos nas cargas altas.

FASE 2 — Métricas e estatística (itens 9 a 13 da revisão)
- Troque o desvio populacional pelo amostral e adicione o intervalo de confiança de 95% (t de Student). Se precisar do scipy, coloque-o só em requirements-dev.txt.
- Conte enlaces saturados também com limiares de 80% e 90%, além de 100%.
- Reporte o índice de Jain por período e a média entre os períodos.
- Remova os arquivos vazios em metrics/ e atualize o README.
- Otimize o NetworkGraph com um dicionário de adjacência, PRESERVANDO a ordem dos vizinhos. Prove que os caminhos e resultados ficam idênticos com a mesma semente antes e depois, comparando as saídas.

FASE 3 — Pipeline de experimentos
- Crie experiments/run_all.py, que roda a matriz topologia × nível de carga × algoritmo × repetições (pelo menos 10).
- Salve tudo em results/<data-hora>/, junto com a config usada e o hash do commit do git.
- Antes da matriz completa, rode uma versão reduzida, estime o tempo total e me informe ANTES de rodar tudo.

FASE 4 — Gráficos e tabelas
- Crie scripts/plots.py com matplotlib (em requirements-dev.txt), gerando figuras em PDF vetorial em results/<execução>/figuras/.
- Gere estes gráficos, com barras de IC 95%: aceitação × carga por algoritmo, banda atendida, utilização média e máxima, saturação, Jain, saltos, taxa de reutilização e tempo de decisão (escala log).
- Gere também tabelas LaTeX compatíveis com abnTeX2 (\caption, \label, \fonte{Elaborado pelo autor.}).

FASE 5 — Texto
- Liste as divergências entre o código e o texto do TCC (itens 3 a 8 da revisão) e me diga, para cada uma, se a sugestão é ajustar o texto ou o código. A regra de reaproveitamento do PETIC (item 4) só muda depois que eu conferir o artigo de Gomes et al. (2018).
- Preencha os [PENDENTE] de docs/tcc/metodologia.tex com os valores reais das configs.
- Escreva um rascunho de docs/tcc/resultados.tex (Resultados e Discussão, em português acadêmico e impessoal, em LaTeX abnTeX2), usando SOMENTE os dados de results/. Cada número citado no texto precisa vir de um arquivo gerado; indique em comentário LaTeX de qual arquivo saiu.

Comece pela leitura e pela Fase 0.
