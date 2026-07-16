# AGENTS.md

## Projeto

Este repositorio representa o DOD Rx, um modulo do ecossistema DOD Performance
focado em leitura assistida de radiografias, especialmente radiografia de torax
no MVP atual.

O projeto deve ser tratado como apoio a decisao clinica, nao como diagnostico
autonomo. Toda saida clinica relevante exige revisao humana.

## Regras permanentes

- Respeitar a ordem conceitual do ecossistema: `dodperformance.main`,
  `dodperformance.clinico`, `dodperformance.rx`.
- Nao alterar o DOD ECG existente para implementar o DOD Rx.
- Usar o DOD ECG apenas como referencia visual, estrutural e autoral de
  dashboard.
- O dashboard do DOD Rx deve herdar o shell visual do ECG, porque esse design
  pertence ao autor do projeto e faz parte da identidade DOD.
- O DOD Rx deve ter motor clinico proprio para radiografia, imagem medica,
  achados, revisao humana e auditoria.
- Nao reenquadrar o DOD Rx como app primario de prescricao, OCR textual ou chat
  clinico. O foco e viewer radiologico, worklist, inferencia de imagem e
  governanca.

## Stack preferida

- Frontend: Next.js, Tailwind e componentes acessiveis.
- Viewer atual: componente local `DicomViewer` com suporte a imagens e DICOM via
  DWV.
- Viewer alvo futuro: OHIF quando a integracao PACS/DICOMweb justificar.
- Backend: FastAPI.
- ML: Python, PyTorch/TorchXRayVision, pipeline de preprocessamento e Grad-CAM.
- Banco: PostgreSQL em ambiente integrado; SQLite pode continuar como caminho
  local/teste.
- PACS/archive alvo futuro: Orthanc com DICOMweb.
- Auditoria: eventos persistidos por estudo, predicao, revisao e acao relevante.

## Regras clinicas e de seguranca

- IA e sempre advisory.
- Nenhum estudo deve ser finalizado sem revisao humana registrada.
- Predicoes antigas nao devem ser sobrescritas; novas inferencias criam novos
  registros.
- Toda predicao deve registrar modelo, versao, timestamp e achados estruturados.
- Toda revisao deve registrar usuario revisor, predicao revisada e divergencias
  relevantes entre IA e humano.
- Achados criticos devem priorizar a worklist e exigir atencao humana.
- Arquivos DICOM devem passar por desidentificacao antes de persistencia.
- Nao remover disclaimers, auditoria ou barreiras de revisao humana para acelerar
  a experiencia.

## Direcao visual

O DOD Rx deve usar o mesmo espirito visual do DOD ECG:

- shell com sidebar/topbar quando o layout for expandido;
- cards executivos, KPIs, badges e paineis laterais;
- dark mode e densidade visual profissional;
- worklist escaneavel;
- painel de achados estruturados;
- historico/auditoria visivel;
- revisao humana como etapa clara do fluxo.

Traducoes conceituais do ECG para RX:

- "Ritmo / FC / Eixo" vira "Modalidade / Projecao / Qualidade tecnica".
- "Interpretacao ECG" vira "Achados sugeridos pela IA".
- "Timeline clinica" vira "Historico de estudos".
- "Risco" vira "Urgencia / triagem / revisao pendente".

## Arquivos de contexto

- `docs/PRD-DOD-RX.md`: produto, usuarios, MVP e fora de escopo.
- `docs/ARCHITECTURE-DOD-RX.md`: arquitetura atual e arquitetura alvo.
- `docs/HANDOFF.md`: estado atual, decisoes tomadas e proxima tarefa.
- `docs/CONTINUITY-WORKFLOW.md`: ordem fixa para continuar sempre de onde parou.
- `docs/TODAY-DOD-RX.md`: acao pratica imediata do projeto.
- `docs/RXAI-TECHNICAL-BLUEPRINT.md`: blueprint tecnico compacto com modulos,
  entidades, endpoints, papeis e traducao de governanca IA.
- `docs/AI-IMAGE-ANALYSIS-WORKFLOW-DOD-RX.md`: ordem operacional para imagem,
  comando de IA, heatmaps, revisao e auditoria.
- `docs/CLINICAL-IMAGE-ARCHITECTURE-DOD-RX.md`: desenho cirurgico da
  arquitetura clinica de imagem, separando imagem, IA, decisao, politica e
  governanca.
- `docs/MEDICAL-ETHICS-LEGAL-POLICY-DOD-RX.md`: base medico-etica, legal e
  academica para IA, politica clinica, revisao humana e uso controlado.

Antes de grandes mudancas, leia estes arquivos junto com `README.md` e
`MODEL_CARD.md`.

## Continuidade obrigatoria

Para qualquer nova etapa, seguir o protocolo em
`docs/CONTINUITY-WORKFLOW.md`. Ao terminar uma etapa relevante, atualizar
`docs/HANDOFF.md` com o que foi feito, verificacoes executadas, pendencias e
proxima acao recomendada.
