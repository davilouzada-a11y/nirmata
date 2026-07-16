# PRD - DOD Rx

## Visao

DOD Rx e uma plataforma web de leitura assistida de radiografias. O objetivo e
ajudar na triagem, visualizacao, estruturacao de achados e revisao humana, sem
substituir o medico.

O produto nasce dentro do ecossistema DOD Performance e deve manter continuidade
visual com o DOD ECG, sem modificar o modulo ECG original.

## Problema

Radiografias precisam de fluxo organizado: entrada do exame, visualizacao,
priorizacao, apoio de IA, revisao humana e auditoria. Um app generico de chat,
OCR ou prescricao nao atende bem esse dominio, porque imagem medica exige viewer,
worklist, pipeline de inferencia, versionamento de modelo e governanca clinica.

## Usuarios

- Radiologista ou medico leitor.
- Estudante/pesquisador em ambiente educacional.
- Operador tecnico ou responsavel por fila RIS/PACS.
- Revisor administrativo de qualidade e seguranca.

## Decisoes fundadoras do MVP

Estas respostas devem orientar produto, design e codigo ate nova decisao
explicita:

- Exame inicial: radiografia de torax.
- Usuario inicial: uso de pesquisa/desenvolvimento pelo autor, com fluxo
  preparado para medico leitor e estudante.
- Saida clinica do MVP: triagem e achados sugeridos pela IA, com probabilidades,
  prioridade e heatmaps quando disponiveis.
- Nao entregar no MVP: laudo autonomo, diagnostico final ou pre-laudo sem
  revisao humana.
- Revisao humana obrigatoria: todo estudo com saida clinica deve ser revisado
  por humano antes de finalizacao; achados criticos e baixa confianca exigem
  atencao prioritaria.

## Objetivos do MVP

- Receber radiografias por upload controlado.
- Renderizar imagem radiografica no navegador.
- Rodar inferencia de IA para escopo inicial de radiografia de torax.
- Apresentar achados estruturados, probabilidades e heatmaps.
- Priorizar achados criticos na worklist.
- Exigir revisao humana antes de finalizar qualquer resultado.
- Registrar auditoria de upload, predicao, revisao e finalizacao.
- Exibir historico operacional do estudo.

## Escopo atual

O repositorio ja contem uma base funcional com:

- frontend Next.js;
- backend FastAPI;
- modelos de estudo, paciente, predicao, revisao, auditoria e usuario;
- workflow clinico `uploaded -> processing -> predicted -> under_review ->
  reviewed -> finalized`;
- inferencia mock, TorchXRayVision e caminho para checkpoint proprio;
- Grad-CAM;
- testes backend e ML;
- validacao documentada em `MODEL_CARD.md` e `ml/validation/`.

## Fora do MVP

- Laudo final autonomo sem humano.
- Uso assistencial real sem validacao clinica, governanca regulatoria e
  autorizacoes necessarias.
- Integracao hospitalar completa com RIS/EHR produtivo.
- Multimodalidade ampla no primeiro ciclo.
- Suporte completo a todos os protocolos radiologicos complexos.
- Substituir o viewer atual por OHIF antes de existir necessidade clara de
  PACS/DICOMweb.

## Principios de produto

- Mesmo dashboard shell, novo motor clinico.
- Visual herdado do DOD ECG; logica clinica recriada para RX.
- IA ajuda a organizar e chamar atencao, nao sentencia sozinha.
- O valor esta no servico ao paciente: clareza, cuidado, rastreabilidade e
  oportunidade de revisao.
- Resultados numericos nao podem apagar contexto humano, limites do modelo e
  responsabilidade clinica.

## Telas esperadas

- Home do modulo com metricas, fila e entrada de estudos.
- Worklist radiografica com filtros por status, prioridade, modalidade e data.
- Viewer + achados com imagem, heatmap, probabilidades e painel lateral.
- Historico do estudo com eventos e versoes de predicao.
- Revisao humana com aceitar/rejeitar achados, observacoes e finalizacao.
- Admin/governanca com modelos, thresholds, regras, auditoria e usuarios.

## Criterios de aceite

- Um estudo pode ser enviado, visualizado, processado, revisado e finalizado.
- Estudos com achado critico sobem prioridade.
- A UI deixa claro que IA e apoio a decisao.
- A finalizacao sem revisao humana deve ser impedida pelo backend.
- O historico de auditoria deve mostrar a sequencia relevante de eventos.
- A identidade visual deve caminhar para o padrao autoral do DOD ECG.
