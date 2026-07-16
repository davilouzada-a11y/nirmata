# Handoff - DOD Rx

## Estado atual

O repositorio `nirmata-main` ja contem uma base funcional de Radiografia AI /
DOD Rx com frontend, backend, ML, revisao humana, auditoria e validacao.

Em 2026-07-10 foram feitas as primeiras passagens visuais do DOD Rx:

- home/worklist aproximada da linguagem do DOD ECG;
- tela de detalhe do estudo aproximada da mesma linguagem, cobrindo achados IA,
  viewer, revisao humana e auditoria.
- telas auxiliares de login e modelos/governanca aproximadas da mesma linguagem.

O contexto de produto definido nas conversas e:

- DOD Rx e um novo modulo de leitura assistida de radiografias.
- O DOD ECG e referencia visual/autoral, mas nao deve ser alterado.
- O DOD Rx deve herdar o shell visual do ECG e trocar completamente a logica
  clinica para radiografia.
- A governanca deve ser inspirada no Nirmata, mas aplicada a modelos, regras,
  thresholds, auditoria e revisao humana de imagem medica.

## Decisoes tomadas

- O produto nao deve ser tratado como app primario de prescricao.
- O foco e radiografia: viewer, worklist, achados, triagem, historico e revisao.
- O exame inicial do MVP e radiografia de torax.
- O usuario inicial e pesquisa/desenvolvimento pelo autor, com fluxo preparado
  para medico leitor e estudante.
- A saida clinica inicial e triagem + achados sugeridos pela IA, nao laudo
  autonomo.
- Next.js + Tailwind continuam como base do frontend.
- FastAPI continua como base do backend.
- O viewer atual pode continuar no MVP; OHIF/Orthanc/DICOMweb sao alvo futuro.
- Revisao humana obrigatoria e regra inegociavel.
- Auditoria e versionamento de modelo fazem parte do nucleo do produto.

## O que nao fazer

- Nao mexer no DOD ECG original.
- Nao remover barreiras de seguranca para parecer mais "automatico".
- Nao prometer diagnostico autonomo.
- Nao substituir o fluxo de imagem medica por chat generico.
- Nao implementar OHIF/Orthanc so por arquitetura ideal se o proximo passo for
  melhorar o MVP existente.

## Proximo passo recomendado

Seguir o protocolo de continuidade em `docs/CONTINUITY-WORKFLOW.md`.
Para a acao imediata, seguir tambem `docs/TODAY-DOD-RX.md`.

A primeira camada visual do DOD Rx foi concluida nas telas principais e
auxiliares. A proxima etapa pratica e revisar estados e fluxo real com backend:

1. Revisar estados vazios/erro/carregamento em outras telas se necessario.
2. Decidir entre refinamento visual fino ou proxima etapa tecnica.
3. Proxima etapa tecnica sugerida: criar mecanismo controlado para nova versao
   de politica clinica ou iniciar preparacao controlada para PACS/OHIF,
   conforme prioridade do autor.
4. Mecanismo controlado de politica clinica foi iniciado no backend:
   criar/ativar politicas agora existe como API protegida por papel e auditada.
5. Primeira versao de divergencia IA versus humano foi criada no backend em
   `/governance/divergence`.
6. Primeira tela de governanca foi criada no frontend em `/governance`.
7. Filtros de governanca foram adicionados para periodo, modelo e politica
   clinica.
8. Entidade `clinical_policy` foi expandida para sustentar etica/governanca
   explicita com nome, status, autor, notas e timestamps de ativacao.
9. Primeira parte do aporte `DOD.clinical_policy` aplicada: `rules` agora
   suporta guardrails explicitos, preservando achados em `rules` serializado
   para compatibilidade da UI.
10. Payload operacional `v1.3.0` de politica clinica foi aceito como draft no
    dev, incluindo regras de triagem, finalizacao, disclaimer e auditoria.
11. Desenho textual cirurgico da arquitetura clinica de imagem foi criado,
    separando imagem, IA advisory, decisao humana, politica clinica e
    governanca.
12. Primeiro ponto cirurgico executavel aplicado: acesso a imagem/heatmap agora
    gera auditoria `image.viewed` e `image.heatmap_viewed`.
13. Segundo ponto cirurgico executavel aplicado: revisao agora registra
    `policy.denied` para bloqueios e `policy.evaluated` para avaliacao
    permitida da politica ativa.

## Ultima etapa executada

- Arquivos alterados:
  - `frontend/app/globals.css`
  - `frontend/app/layout.tsx`
  - `frontend/app/page.tsx`
  - `frontend/app/components/StatsPanel.tsx`
  - `frontend/app/components/StudyQueue.tsx`
  - `frontend/app/studies/[id]/page.tsx`
  - `frontend/app/components/FindingList.tsx`
  - `frontend/app/components/ReviewForm.tsx`
  - `frontend/app/components/AuditTimeline.tsx`
  - `frontend/app/components/DicomViewer.tsx`
  - `frontend/app/components/HeatmapOverlayToggle.tsx`
  - `frontend/app/login/page.tsx`
  - `frontend/app/models/page.tsx`
  - `frontend/next.config.mjs`
  - `frontend/package.json`
  - `frontend/package-lock.json`
- O que mudou:
  - shell superior DOD Rx com marca DOD Performance;
  - fundo dark com grid tecnico inspirado no DOD ECG;
  - hero funcional da worklist, sem virar landing page;
  - painel de governanca clinica;
  - cards KPI em superfice translucida;
  - formulario de upload e tabela com linguagem visual do ECG.
  - tela de detalhe com cabecalho de estudo, badges, achados IA, viewer,
    revisao humana e auditoria no mesmo sistema visual;
  - login redesenhado como porta de entrada DOD Rx;
  - modelos redesenhado como governanca de modelos/thresholds;
  - alias do DWV no Next para usar o bundle browser tambem no dev server.
  - imagens PNG/JPG e heatmaps agora sao carregados no viewer com `fetch`
    autenticado e `blob:` URL, preservando endpoints protegidos por JWT.
  - tela de detalhe evita chamadas prematuras a predicao/revisao quando o estudo
    ainda esta apenas `uploaded`, reduzindo 404 esperados no fluxo novo.
  - upload real pela UI foi validado com imagem PNG sintetica, seguido de
    inferencia, revisao humana e auditoria.
  - worklist refinada para responsividade: tabela preservada em desktop e
    cards compactos em mobile, sem depender de rolagem horizontal.
  - estados de loading/erro/vazio adicionados para worklist.
  - estados de loading/erro adicionados para KPIs da home.
  - roteiro `docs/DICOM-LOCAL-VALIDATION.md` criado para prova DICOM local com
    DICOM sintetico, desidentificacao, auditoria e criterios de aceite.
  - upload DICOM pelo fluxo visual real da aplicacao foi validado com DICOM
    sintetico e usuario radiologista local.
  - formularios de login e upload receberam associacao acessivel entre `label`
    e campos (`htmlFor`/`id`), autocomplete no login e descricao acessivel para
    o campo de arquivo.
  - revisao humana ganhou painel governado com comparacao "IA sugeriu" versus
    "Medico decidiu", contagem de divergencias e comentario por achado.
  - tela de estudo finalizado agora mostra resumo de revisao com decisao,
    divergencias, comentarios e comparacao por achado.
  - tela de governanca de modelos passou a destacar modelo ativo, quantidade de
    thresholds versionados, regras criticas e tabela de thresholds por achado.
  - pneumotorax aparece como regra critica que prioriza worklist.
  - regras clinicas foram separadas dos thresholds/modelo em
    `backend/app/services/clinical_policy.py`.
  - novo endpoint `GET /models/policy/active` expoe politica clinica versionada
    com escopo, revisao humana obrigatoria, bloqueio de diagnostico autonomo,
    achados criticos e regras por achado.
  - frontend passou a consumir a politica ativa em `/models` em vez de manter
    regra critica hardcoded na tela.
  - politicas clinicas agora sao persistidas na tabela `clinical_policies`, com
    migration Alembic, flag `active`, regras JSON, revisao humana obrigatoria,
    diagnostico autonomo bloqueado e regra de finalizacao.
  - `python -m app.seed` cria/ativa a politica padrao
    `dod-rx-cxr-policy-v0.1.0`.
  - payload de auditoria `study.predict` registrava `clinical_policy_version`
    junto com `model_version`; isso foi corrigido depois para manter politica
    clinica no eixo de decisao/revisao, nao de inferencia.
  - revisoes humanas agora persistem `clinical_policy_version` na tabela
    `reviews`.
  - payload de auditoria `study.review` tambem registra
    `clinical_policy_version`.
  - resumo da revisao na tela do estudo exibe a politica clinica usada.
  - documento `docs/MEDICAL-ETHICS-LEGAL-POLICY-DOD-RX.md` criado como base
    medico-etica, legal e academica para IA, politica clinica, revisao humana,
    privacidade e uso controlado.
  - `AGENTS.md` atualizado para tornar esse documento referencia obrigatoria em
    mudancas grandes.
  - endpoint `GET /models/policies` criado para listar historico de politicas
    clinicas versionadas.
  - tela `/models` passou a exibir bloco "Historico de politicas clinicas" com
    versao, escopo, quantidade de regras, regras criticas, estado ativo e data
    de criacao.
  - `docs/RXAI-TECHNICAL-BLUEPRINT.md` criado com blueprint tecnico compacto:
    entidades, endpoints, papeis, workflow e traducao Nirmata/Kyverno para
    governanca de modelos clinicos RX.
  - `docs/AI-IMAGE-ANALYSIS-WORKFLOW-DOD-RX.md` criado com a ordem oficial de
    upload, validacao de imagem, comando de IA, predicao, viewer, heatmap,
    revisao humana, finalizacao e auditoria.
  - `docs/RXAI-AGENTS-SKELETON.md` e `docs/RXAI-HANDOFF-SKELETON.md` criados
    como esqueletos prontos para repositorio RX.AI.
  - `AGENTS.md` atualizado para referenciar blueprint tecnico e workflow
    IA+imagem como contexto obrigatorio.
  - endpoint `POST /models/policies` criado para registrar nova politica
    clinica versionada com guardrails obrigatorios.
  - endpoint `POST /models/policies/{id}/activate` criado para ativar politica
    clinica com permissao de governanca e auditoria.
  - mudancas de politica clinica agora exigem papel `admin` ou
    `admin_clinical`.
  - validacao de seguranca impede criar/ativar politica que desligue revisao
    humana, permita diagnostico autonomo ou finalize sem revisao humana.
  - eventos `policy.create` e `policy.activate` sao registrados na auditoria.
  - seed local passou a criar usuario de governanca clinica
    `governanca@example.com` com papel `admin_clinical`.
  - modulo `backend/app/api/governance.py` criado com endpoint
    `GET /governance/divergence`.
  - relatorio de divergencia consolida revisoes, achados revisados,
    divergencias, taxa de divergencia, decisoes, breakdown por achado,
    model version, politica clinica e casos criticos de pneumotorax.
  - frontend passou a consumir `GET /governance/divergence`.
  - tela `frontend/app/governance/page.tsx` criada com KPIs de divergencia,
    leitura executiva, tabela por achado, blocos por decisao/modelo/politica e
    casos criticos.
  - navegacao principal e home passaram a incluir acesso para `Governança`.
  - fluxo de login passou a preservar destino protegido com `?next=...`; ao
    abrir `/governance` sem token, o usuario vai para `/login?next=/governance`
    e retorna para `/governance` apos autenticar.
  - endpoint `GET /governance/divergence` passou a aceitar filtros opcionais:
    `from`, `to`, `model_version` e `clinical_policy_version`.
  - tela `/governance` ganhou filtros de data inicial/final, modelo, politica e
    botao para limpar filtros.
  - tabela `clinical_policies` ganhou campos `name`, `status`, `updated_at`,
    `activated_at`, `created_by_user_id` e `notes`.
  - politicas clinicas agora seguem status `draft`, `active` e `retired`, sem
    apagar historico.
  - criacao de politica registra autor (`created_by_user_id`) e notas livres.
  - ativacao marca a politica como `active`, preenche `activated_at` e aposenta
    as demais como `retired`.
  - tela `/models` passou a exibir nome e status real das politicas clinicas.
  - API de politicas passou a devolver `rule_guardrails` com
    `must_have_human_review`, `allow_autonomous_diagnosis`,
    `max_autoclose_without_review_minutes`,
    `critical_findings_require_review` e
    `allowed_workflow_states_for_auto_actions`.
  - validacao de politica agora rejeita tambem guardrails explicitos inseguros,
    nao apenas os aliases legados `human_review_required` e
    `autonomous_diagnosis_allowed`.
  - guardrails operacionais adicionados:
    `triage_priority_rules`, `finalization_rules`, `disclaimer_rules` e
    `audit_rules`.
  - tela `/models` passou a exibir o texto de banner vindo de
    `disclaimer_rules.banner_text` quando disponivel.
  - `study.predict` deixou de registrar `clinical_policy_version`; a politica
    clinica fica no eixo de revisao/finalizacao, conforme escopo
    `DOD.clinical_policy`.
  - documento `docs/CLINICAL-IMAGE-ARCHITECTURE-DOD-RX.md` criado com desenho
    textual da arquitetura: frontend Next.js, backend FastAPI, storage
    protegido, servico ML, revisao humana, politica clinica e governanca.
  - `AGENTS.md` e `docs/RXAI-TECHNICAL-BLUEPRINT.md` passaram a referenciar a
    arquitetura clinica de imagem.
  - endpoint `GET /studies/{id}/image` passou a registrar auditoria
    `image.viewed`.
  - endpoint `GET /studies/{id}/heatmaps/{finding_code}` passou a registrar
    auditoria `image.heatmap_viewed`.
  - `review_service.create_review` passou a registrar `policy.denied` quando a
    revisao e bloqueada por estado invalido ou predicao ausente.
  - `review_service.create_review` passou a registrar `policy.evaluated` quando
    a politica ativa permite a revisao humana antes da finalizacao.
- Verificacoes executadas:
  - `npm ci`
  - `npm run build`
  - backend local com SQLite: `alembic upgrade head` e `python -m app.demo`
  - testes backend: `pytest -q` com 9 testes passando;
  - fluxo real com backend/frontend: login, worklist, detalhe do estudo,
    achados, revisao humana e auditoria;
  - fluxo real de upload pela UI;
  - verificacao real de imagem e heatmap autenticados no viewer;
  - checagem de estudo recem-enviado sem chamadas prematuras a
    `/prediction`/`/review`;
  - Playwright desktop com API simulada;
  - Playwright mobile com API simulada.
  - Playwright desktop/mobile com API simulada apos responsividade da worklist,
    validando tabela no desktop, cards no mobile e ausencia de overflow
    horizontal em 390px.
  - `pytest -q` no backend com 9 testes passando, incluindo DICOM desidentificado,
    DICOM corrompido rejeitado, auditoria, re-predicao e revisao humana.
  - CLI de preprocessamento validado com DICOM sintetico:
    `python -m ml.preprocessing --make-sample /tmp/dod-rx-sample.dcm` e
    `python -m ml.preprocessing --in /tmp/dod-rx-sample.dcm --out-dir /tmp/dod-rx-preprocessed --salt local-dev`.
  - fluxo UI real com DICOM sintetico: login, upload `.dcm`, abertura do estudo,
    viewer DWV sem erro, inferencia, revisao humana e auditoria.
  - estudo DICOM validado no backend apos UI: status `finalized`,
    `image_format=dicom`, `PatientIdentityRemoved=YES`, `PatientName`
    pseudonimizado, sem `InstitutionName`, sem `DeviceSerialNumber`, e auditoria
    com `study.upload`, `study.deidentify`, `study.predict` e `study.review`.
  - `npm run build`.
  - QA Playwright desktop/mobile para acessibilidade dos formularios:
    `getByLabel("E-mail")`, `getByLabel("Senha")`,
    `getByLabel("Código do paciente")`, `getByLabel("Incidência")` e
    `getByLabel("Imagem (DICOM/PNG/JPG)")` funcionando, sem erros de console e
    sem overflow horizontal em 390px.
  - `npm run build` apos painel de revisao governada.
  - QA Playwright do fluxo UI: login, upload PNG, abertura do estudo, inferencia,
    correcao de achado, comentario por achado e revisao finalizada. A tela
    reaberta exibiu decisao `corrected`, `1 DIVERGÊNCIA`, comparacao IA/Medico
    e comentario do revisor.
  - `npm run build` apos governanca de modelos/thresholds.
  - QA Playwright desktop/mobile em `/models`: modelo ativo, thresholds
    versionados, regra critica `prioriza`, politica de revisao humana, ausencia
    de erro de console e ausencia de overflow horizontal em 390px.
  - `pytest -q` no backend com 9 testes passando apos separacao de politica.
  - `npm run build` apos cliente/tela consumirem politica ativa.
  - endpoint `GET /models/policy/active` validado com usuario radiologista local,
    retornando `dod-rx-cxr-policy-v0.1.0`.
  - QA Playwright em `/models` confirmou versao da politica, bloco de politica
    clinica versionada, HITL obrigatorio e regra critica `prioriza`, sem erros
    de console.
  - `alembic upgrade head` aplicado com migration
    `1f6a2c9e7b31_add_clinical_policies.py`.
  - `pytest -q` com 9 testes passando apos persistencia de politica clinica.
  - `npm run build` apos ajuste de API/frontend.
  - endpoint `/models/policy/active` validado retornando politica com `id`,
    `active=true`, 6 regras e `human_review_required=true`.
  - `alembic upgrade head` aplicado com migration
    `7c4f9d1a2e83_add_policy_version_to_reviews.py`.
  - `pytest -q` com 9 testes passando apos `clinical_policy_version` em
    revisoes.
  - `npm run build` apos exibicao da politica no resumo da revisao.
  - fluxo API validado: upload, predicao e revisao retornando
    `clinical_policy_version=dod-rx-cxr-policy-v0.1.0` na revisao e auditoria.
  - QA Playwright em estudo finalizado confirmou decisao e politica clinica no
    resumo da revisao, sem erros de console.
  - revisao documental: politica medico-etica/legal/academica registrada em
    Markdown e ligada ao contexto persistente do projeto.
  - `pytest -q` com 9 testes passando apos listagem de politicas.
  - `npm run build` apos historico de politicas no frontend.
  - endpoint `/models/policies` validado retornando 1 politica ativa,
    `dod-rx-cxr-policy-v0.1.0`, com 6 regras.
  - QA Playwright em `/models` confirmou historico de politicas, versao ativa,
    ausencia de overflow horizontal e ausencia de erros de console.
  - revisao documental dos artefatos RX.AI: blueprint tecnico, workflow
    IA+imagem e esqueletos AGENTS/HANDOFF criados em Markdown.
  - `pytest -q` com 12 testes passando apos endpoints controlados de politica
    clinica, incluindo criacao, ativacao, bloqueio por papel, guardrails e
    auditoria.
  - dev local validado em `http://127.0.0.1:8000`: login de governanca,
    listagem de politicas e criacao da politica inativa
    `dod-rx-cxr-policy-dev-v0.1.1`.
  - `pytest -q` com 13 testes passando apos endpoint de divergencia
    IA-humano.
  - endpoint local `GET /governance/divergence` validado com usuario
    radiologista, retornando 7 revisoes, 42 achados revisados, 1 divergencia e
    taxa de divergencia `0.0238` no banco de desenvolvimento atual.
  - `npm run build` passando apos tela `/governance`.
  - QA Playwright em `/governance` desktop/mobile: heading, metricas e bloco
    por achado renderizados; sem overflow horizontal em 1440px e 390px.
  - `npm run build` passando apos fluxo de login com `next`.
  - QA Playwright validou `/governance` sem token -> `/login?next=/governance`
    -> login -> retorno automatico para `/governance`.
  - `pytest -q` com 13 testes passando apos filtros do endpoint de divergencia.
  - `npm run build` passando apos filtros de `/governance`.
  - QA Playwright desktop/mobile validou selecao de modelo e politica
    `unknown_policy`, resposta filtrada da API e ausencia de overflow
    horizontal.
  - migration `2e3f4a5b6c7d_expand_clinical_policy_metadata.py` aplicada no
    SQLite local.
  - criacao real de politica draft validada no dev:
    `dod-rx-cxr-policy-dev-v0.1.2`, com `name`, `status=draft`,
    `created_by_user_id` e `notes`.
  - `pytest -q` com 13 testes passando apos metadados de politica.
  - `npm run build` passando apos exibicao de nome/status em `/models`.
  - `pytest -q` com 13 testes passando apos guardrails explicitos em `rules`.
  - `npm run build` passando apos tipo `rule_guardrails` no frontend.
  - API `/models/policies` validada retornando `rule_guardrails`.
  - politica draft `v1.3.0` criada no dev com escopo
    `clinical_rx_triage`, guardrails completos e status `draft`.
  - `pytest -q` com 13 testes passando apos guardrails operacionais.
  - `npm run build` passando apos banner vindo da politica em `/models`.
  - revisao documental da arquitetura clinica de imagem registrada em Markdown.
  - validacao em 2026-07-15: backend/frontend subidos, `/health` OK,
    `/models/policies` retornando `v1.3.0` como `draft` com `rule_guardrails`,
    `/governance/divergence?clinical_policy_version=v1.3.0` retornando zero
    revisoes como esperado para politica ainda nao ativa.
  - QA Playwright mobile em `/models` e `/governance` sem overflow horizontal.
  - `pytest -q` com 13 testes passando apos auditoria `image.viewed`.
  - `pytest -q` com 13 testes passando apos auditoria
    `policy.evaluated/policy.denied`.
  - endpoints backend `POST /studies/{id}/hold` e
    `POST /studies/{id}/reopen` adicionados com justificativa obrigatoria,
    bloqueio de revisao enquanto `status=blocked` e auditoria
    `study.hold`/`study.reopened`.
  - `pytest -q` com 14 testes passando apos estados `hold/reopen`.
  - validacao dev real: upload -> predict -> hold (`blocked`) -> review
    bloqueada com 409 -> reopen (`predicted`) com auditoria
    `study.upload`, `study.predict`, `study.hold`, `policy.denied` e
    `study.reopened`.
- Observacoes:
  - Playwright foi adicionado como dependencia de desenvolvimento para permitir
    verificacao visual local.
  - O `npm ci`/auditoria apontou 2 vulnerabilidades herdadas do conjunto atual;
    nao foi aplicado `npm audit fix --force` para evitar alteracoes de versoes
    fora de escopo.
  - Python local disponivel era 3.14; para rodar o backend com SQLite local foi
    criada `backend/.venv` com dependencias atuais compativeis, sem instalar
    `psycopg2-binary` porque ele exigiu `pg_config` nessa versao do Python.
  - O navegador interno (`iab`) nao estava disponivel na sessao de QA de
    acessibilidade; a validacao renderizada foi feita por Playwright local.
  - Durante hot reload do Next dev, o cache `.next` corrompeu um chunk
    temporario; foi necessario parar o frontend, remover `.next` e reiniciar o
    dev server. O build de producao estava passando antes e depois.
  - Banco local de desenvolvimento contem uma politica extra inativa
    `dod-rx-cxr-policy-dev-v0.1.1`, criada apenas para validar o endpoint.
  - Banco local tambem contem a politica draft
    `dod-rx-cxr-policy-dev-v0.1.2`, criada para validar metadados eticos de
    politica.
  - Banco local contem tambem a politica draft `v1.3.0`, criada a partir do
    aporte operacional de `DOD.clinical_policy`.
  - A partir da primeira parte do aporte DOD.clinical_policy, predicoes seguem
    registrando modelo/metadados de inferencia; `clinical_policy_version` fica
    registrado na revisao/finalizacao e nos relatorios de divergencia.
  - O banco local ainda contem revisoes antigas com
    `clinical_policy_version=null`; no relatorio de divergencia elas aparecem
    como `unknown_policy`, esperado para dados anteriores a persistencia da
    politica clinica em revisoes.
  - Durante QA do Next dev apos reinicio, apareceu um erro transitorio de
    Fast Refresh/RSC no console; a pagina renderizou, nao houve overflow, e o
    build de producao passou.
  - Quando o Next dev corromper chunks em hot reload, parar o frontend, remover
    `frontend/.next` e reiniciar `npm run dev -- --hostname 127.0.0.1 --port 3000`.

## Comando de orientacao para agentes

Antes de comecar uma tarefa grande, leia:

- `AGENTS.md`
- `docs/HANDOFF.md`
- `docs/CONTINUITY-WORKFLOW.md`
- `docs/TODAY-DOD-RX.md`
- `docs/DICOM-LOCAL-VALIDATION.md`
- `docs/RXAI-TECHNICAL-BLUEPRINT.md`
- `docs/AI-IMAGE-ANALYSIS-WORKFLOW-DOD-RX.md`
- `docs/MEDICAL-ETHICS-LEGAL-POLICY-DOD-RX.md`
- `docs/PRD-DOD-RX.md`
- `docs/ARCHITECTURE-DOD-RX.md`
- `README.md`
- `MODEL_CARD.md`, quando a tarefa tocar IA, validacao, risco clinico ou
  conclusoes medicas.

Depois execute a menor mudanca concreta que avance o DOD Rx sem quebrar a base
clinica ja existente.

## Proxima acao recomendada apos 2026-07-13

1. Avaliar se a criacao/ativacao de politica clinica precisa aparecer na UI ou
   permanecer apenas como API governada.
2. Depois considerar endpoint/tela de incidentes de governanca.
3. Se a UI pedir, expor `hold/reopen` na tela do estudo com campo de
   justificativa obrigatoria.
