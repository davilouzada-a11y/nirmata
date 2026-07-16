# HANDOFF.md - RX.AI

Use este conteudo como esqueleto de handoff para um repositorio RX.AI.

## O que e

RX.AI e um sistema web de apoio a decisao para radiografia de torax com upload
de estudo, inferencia por IA, heatmaps, fila clinica, auditoria, politica
clinica versionada e revisao humana obrigatoria antes da finalizacao.

## Estado atual

- Frontend, backend, ML e docs separados.
- Auth local com usuario radiologista seed.
- Upload DICOM/PNG/JPG.
- DICOM desidentificado antes de persistencia.
- Worklist com prioridade clinica.
- Viewer de imagem/DICOM e heatmap.
- Inferencia cria nova predicao.
- Revisao humana compara IA versus medico.
- Auditoria registra upload, de-id, predicao e revisao.
- Modelo e politica clinica sao versionados.

## Decisoes tomadas

- IA nao e diagnostico autonomo.
- Revisao humana e obrigatoria.
- DOD Performance e referencia visual/arquitetural, nao dependencia de codigo.
- Politica clinica e separada dos thresholds do modelo.
- Uso inicial e pesquisa/desenvolvimento/ensino controlado.

## O que nao fazer

- Nao remover disclaimers, auditoria ou barreiras de revisao.
- Nao sobrescrever predicoes antigas.
- Nao persistir DICOM bruto com PHI.
- Nao transformar heatmap em prova diagnostica.
- Nao acoplar RX.AI ao codigo do DOD Performance.
- Nao promover uso clinico sem validacao, governanca e avaliacao adequada.

## Contratos importantes

- `POST /studies/upload`
- `GET /studies`
- `GET /studies/{id}`
- `POST /studies/{id}/predict`
- `GET /studies/{id}/prediction`
- `POST /studies/{id}/review`
- `GET /studies/{id}/review`
- `GET /audit/studies/{id}`
- `GET /models/versions`
- `GET /models/policy/active`
- `GET /models/policies`

## Ultima etapa executada

Preencher sempre:

- arquivos alterados;
- o que mudou;
- verificacoes executadas;
- pendencias;
- proxima acao recomendada.

## Verificacoes minimas

- `pytest -q` no backend quando tocar API/workflow/politica.
- `npm run build` quando tocar frontend.
- QA Playwright quando tocar tela/fluxo renderizado.
- Validar auditoria quando tocar predicao/revisao/politica.
- Atualizar docs quando tocar governanca ou regras clinicas.

## Proxima acao recomendada

Escolher uma:

1. criar mecanismo controlado para nova versao de politica clinica;
2. criar dashboard de divergencia IA-humano;
3. criar incidentes/bloqueios de politica;
4. preparar PACS/OHIF de forma controlada.

## Como retomar

1. Ler `AGENTS.md`.
2. Ler este `HANDOFF.md`.
3. Ler `RXAI-TECHNICAL-BLUEPRINT.md`.
4. Ler `MEDICAL-ETHICS-LEGAL-POLICY-DOD-RX.md`.
5. Fazer a menor mudanca concreta que preserve seguranca clinica.

