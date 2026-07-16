# AGENTS.md - RX.AI

Use este conteudo como esqueleto para um `AGENTS.md` de repositorio RX.AI.

## Projeto

RX.AI e um modulo isolado de apoio a decisao para radiografia de torax, com
upload de imagem, viewer, inferencia por IA, heatmaps, revisao humana
obrigatoria, auditoria e governanca clinica.

O sistema nao e diagnostico autonomo. A decisao clinica final pertence ao medico
revisor.

## Regras imutaveis

- Nao alterar DOD Performance a partir deste repositorio.
- Nao acoplar RX.AI fisicamente a `dodperformance.main`, `clinico` ou `ecg`.
- Integracao futura com DOD deve ocorrer por contrato: link, API, gateway,
  eventos, embed ou SSO.
- IA e sempre advisory.
- Revisao humana e obrigatoria antes de finalizacao.
- DICOM deve ser desidentificado antes de persistencia.
- Predicoes antigas nao devem ser sobrescritas.
- Toda predicao registra `model_version` e metadados de inferencia.
- Toda revisao registra medico revisor, decisao, divergencias e
  `clinical_policy_version`.
- Politica clinica deve ser separada de thresholds do modelo.

## Stack

- Frontend: Next.js App Router + Tailwind.
- Backend: FastAPI.
- Banco: PostgreSQL alvo; SQLite permitido para local/testes.
- ML: Python, preprocessamento DICOM, inferencia, Grad-CAM e validacao.
- Viewer MVP: componente local/DWV.
- Viewer futuro: OHIF quando houver PACS/DICOMweb.

## Modulos

- `frontend`: worklist, upload, viewer, heatmap, revisao e governanca.
- `backend`: auth, estudos, predicao, revisao, auditoria, modelos e politicas.
- `ml`: preprocessamento, inferencia, validacao e treinamento.
- `docs`: PRD, arquitetura, handoff, politica etica/legal e blueprint.

## Regras clinicas

- Nenhum estudo finaliza sem revisao humana.
- Achados criticos priorizam worklist, nao automatizam conduta.
- Heatmap e apoio visual, nao prova diagnostica.
- Probabilidade e triagem, nao laudo.
- Divergencia IA-humano deve ser registrada.
- Mudanca de politica clinica exige nova versao.
- Uso clinico fora de pesquisa exige validacao, governanca e avaliacao
  regulatoria/institucional.

## Arquivos obrigatorios de contexto

- `docs/HANDOFF.md`
- `docs/RXAI-TECHNICAL-BLUEPRINT.md`
- `docs/AI-IMAGE-ANALYSIS-WORKFLOW-DOD-RX.md`
- `docs/MEDICAL-ETHICS-LEGAL-POLICY-DOD-RX.md`
- `docs/DICOM-LOCAL-VALIDATION.md`
- `README.md`
- `MODEL_CARD.md`

## Ordem ao modificar codigo

1. Ler handoff e documentos de politica.
2. Fazer menor mudanca segura.
3. Preservar auditoria, revisao humana e versionamento.
4. Rodar testes proporcionais.
5. Atualizar docs impactadas.
6. Nao introduzir acoplamento com DOD Performance.

## Preferencias de decisao

- Preferir rastreabilidade.
- Preferir bloqueio seguro a automacao arriscada.
- Preferir backend como fonte de verdade.
- Preferir politicas versionadas a regra hardcoded.
- Preferir linguagem clinica explicita.
