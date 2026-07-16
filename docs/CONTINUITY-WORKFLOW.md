# Workflow de Continuidade - DOD Rx

Este arquivo define a ordem fixa para continuar o projeto sempre de onde parou.
Ele deve ser lido antes de qualquer nova etapa de implementacao, design,
arquitetura ou produto.

## Ordem fixa de leitura

Sempre iniciar lendo, nesta ordem:

1. `AGENTS.md`
2. `docs/HANDOFF.md`
3. `docs/CONTINUITY-WORKFLOW.md`
4. `docs/TODAY-DOD-RX.md`
5. `docs/PRD-DOD-RX.md`
6. `docs/ARCHITECTURE-DOD-RX.md`
7. `README.md`
8. `MODEL_CARD.md`, quando a tarefa tocar IA, validacao, risco clinico ou
   conclusoes medicas.

## Ordem fixa de decisao

Antes de executar qualquer mudanca, decidir nesta ordem:

1. Qual foi a ultima etapa registrada no `HANDOFF.md`.
2. Qual e o menor proximo passo concreto.
3. Se a mudanca preserva as regras do `AGENTS.md`.
4. Se a mudanca respeita o PRD e o escopo do MVP.
5. Se a mudanca altera frontend, backend, ML, governanca ou documentacao.
6. Quais testes ou verificacoes sao proporcionais ao risco.

## Perguntas fundadoras

Se uma nova tarefa mudar produto, escopo clinico ou experiencia principal,
confirmar estas quatro respostas antes de codar:

1. Qual exame entra primeiro?
2. Quem usa primeiro?
3. O que a IA entrega no MVP?
4. Qual nivel de revisao humana sera obrigatorio?

Respostas atuais:

1. Exame inicial: radiografia de torax.
2. Usuario inicial: pesquisa/desenvolvimento pelo autor, preparado para medico
   leitor e estudante.
3. Saida IA do MVP: triagem e achados sugeridos, com probabilidades, prioridade
   e heatmaps quando disponiveis.
4. Revisao humana: obrigatoria antes de qualquer finalizacao; achados criticos
   e baixa confianca exigem prioridade.

## Ordem fixa de execucao

Quando houver implementacao, seguir esta sequencia:

1. Ler o codigo existente antes de editar.
2. Fazer mudancas pequenas e integradas.
3. Preservar o fluxo clinico atual.
4. Preservar revisao humana obrigatoria, auditoria e disclaimers.
5. Testar ou validar a parte alterada.
6. Atualizar o `HANDOFF.md` no final da etapa.

## Registro de parada

Ao finalizar uma etapa, atualizar o `HANDOFF.md` com:

- o que foi feito;
- arquivos principais alterados;
- verificacoes executadas;
- pendencias;
- proxima acao recomendada.

Se a etapa nao for concluida, registrar exatamente onde parou e qual e o bloqueio.

## Fila macro do projeto

Seguir esta ordem de evolucao, salvo pedido explicito em contrario:

1. Consolidar contexto persistente e regras de continuidade.
2. Fixar as respostas fundadoras do MVP.
3. Inspecionar o DOD ECG sem altera-lo.
4. Mapear tokens visuais do ECG para o DOD Rx.
5. Aplicar o shell visual autoral ao dashboard DOD Rx.
6. Melhorar worklist, filtros, cards e estados clinicos.
7. Melhorar viewer + painel de achados.
8. Melhorar revisao humana e auditoria.
9. Organizar admin/governanca de modelos, thresholds e politicas.
10. Avaliar necessidade real de OHIF/Orthanc/DICOMweb.
11. Preparar trilha de validacao e documentacao regulatoria futura.

## Primeira acao atual

A primeira acao depois deste protocolo e:

1. Manter como decisao-base: DOD Rx MVP = radiografia de torax para triagem e
   achados sugeridos, com visual herdado do DOD ECG e revisao humana
   obrigatoria.
2. Inspecionar visualmente `../dodperformance-main` para entender o shell do ECG.
3. Mapear cores, espacamento, topbar/sidebar, cards, KPIs, badges e densidade.
4. Aplicar uma primeira passagem visual no DOD Rx sem mexer no DOD ECG.

## Regra de continuidade humana

O projeto deve continuar como servico: clareza, cuidado, rastreabilidade e
respeito ao paciente. Resultado, nota ou metrica nao devem apagar processo,
contexto humano, revisao e responsabilidade.
