# RX.AI - Blueprint Tecnico Compacto

RX.AI e um modulo isolado de apoio a decisao para radiografia de torax. Ele usa
a linguagem visual/estrutural do ecossistema DOD como referencia, mas mantem
codigo, banco, auditoria, IA e politica clinica independentes.

## Principios

- IA e apoio a decisao, nao diagnostico autonomo.
- Revisao humana e obrigatoria antes de finalizacao.
- DICOM deve ser desidentificado antes de persistencia.
- Predicoes nunca sao sobrescritas; cada inferencia cria novo registro.
- Toda predicao registra `model_version` e metadados de inferencia.
- Toda revisao/finalizacao registra medico revisor, decisao, divergencias e
  `clinical_policy_version`.
- Politica clinica e separada de thresholds do modelo.
- DOD Performance nao deve ser alterado por este repositorio.

## Modulos

| Modulo | Papel |
|---|---|
| `frontend` | Worklist, upload, viewer, heatmap, achados IA, revisao humana, auditoria e governanca. |
| `backend` | Auth, estudos, workflow, inferencia, revisao, auditoria, modelos e politicas clinicas. |
| `ml` | Preprocessamento, DICOM de-id, inferencia, Grad-CAM, validacao e treinamento. |
| `docs` | PRD, arquitetura, handoff, politica medico-etica, validacao DICOM e blueprint. |

## Entidades

| Entidade | Campos principais | Papel |
|---|---|---|
| `User` | `id`, `name`, `email`, `role`, `active` | Identidade e permissao. |
| `Patient` | `id`, `external_code`, `anonymized_flag` | Pseudonimo/codigo do paciente. |
| `Study` | `id`, `patient_code`, `modality`, `body_part`, `view`, `status`, `image_format`, `image_path` | Estudo de imagem e estado clinico. |
| `ModelVersion` | `id`, `name`, `version`, `training_dataset`, `threshold_config` | Versao do modelo e thresholds. |
| `ClinicalPolicy` | `id`, `name`, `version`, `scope`, `status`, `active`, `rules`, `human_review_required`, `autonomous_diagnosis_allowed`, `finalization_rule`, `created_by_user_id`, `notes`, `created_at`, `updated_at`, `activated_at` | Regras clinicas, operacionais e de governanca versionadas. |
| `Prediction` | `id`, `study_id`, `model_version_id`, `overall_status`, `inference_time_ms` | Resultado de inferencia versionado. |
| `PredictionFinding` | `prediction_id`, `finding_code`, `probability`, `threshold`, `is_positive`, `heatmap_path` | Achado por classe. |
| `Review` | `study_id`, `prediction_id`, `reviewer_id`, `decision`, `clinical_policy_version`, `final_report` | Decisao humana final. |
| `ReviewFinding` | `review_id`, `finding_code`, `final_label`, `diverged_from_ai`, `comment` | Comparacao IA versus medico. |
| `AuditLog` | `user_id`, `action`, `entity`, `entity_id`, `payload`, `created_at` | Trilha auditavel. |

## Workflow de Estados

```text
uploaded -> processing -> predicted -> under_review -> reviewed -> finalized
```

No MVP atual, o backend usa principalmente:

```text
uploaded -> processing -> predicted -> finalized
```

com revisao humana obrigatoria antes de `finalized`.

Regras:

- `uploaded`: estudo criado apos upload valido.
- `processing`: inferencia em andamento.
- `predicted`: predicao persistida e disponivel para revisao.
- `finalized`: revisao humana registrada.
- Estados futuros recomendados: `blocked`, `failed`, `under_review`,
  `needs_double_review`.

## Arquitetura Clinica de Imagem

O desenho cirurgico de camadas esta em
`docs/CLINICAL-IMAGE-ARCHITECTURE-DOD-RX.md`.

Resumo:

```text
Frontend Next.js
  -> Backend FastAPI
    -> Storage protegido de imagem/DICOM
    -> Servico de ML advisory
    -> Revisao humana
    -> Politica clinica versionada
    -> Auditoria e governanca
```

Regra central: nao existe caminho direto `imagem -> laudo` ou
`IA -> finalizacao`.

## Endpoints Atuais

| Metodo | Endpoint | Papel |
|---|---|---|
| `POST` | `/auth/login` | Login OAuth2 form. |
| `POST` | `/auth/login/json` | Login JSON para frontend. |
| `GET` | `/auth/me` | Usuario atual. |
| `POST` | `/studies/upload` | Upload DICOM/PNG/JPG. |
| `GET` | `/studies` | Worklist. |
| `GET` | `/studies/stats` | KPIs operacionais. |
| `GET` | `/studies/{id}` | Detalhe do estudo. |
| `GET` | `/studies/{id}/image` | Imagem protegida. |
| `POST` | `/studies/{id}/predict` | Criar nova inferencia. |
| `GET` | `/studies/{id}/prediction` | Predicao mais recente. |
| `GET` | `/studies/{id}/heatmaps/{finding_code}` | Heatmap por achado. |
| `POST` | `/studies/{id}/review` | Revisao humana. |
| `GET` | `/studies/{id}/review` | Revisao final. |
| `POST` | `/studies/{id}/hold` | Reter caso por risco, incerteza ou politica, com justificativa auditada. |
| `POST` | `/studies/{id}/reopen` | Reabrir caso retido com justificativa auditada. |
| `GET` | `/audit/studies/{id}` | Auditoria do estudo. |
| `GET` | `/models/versions` | Registry de modelos. |
| `GET` | `/models/policy/active` | Politica clinica ativa. |
| `GET` | `/models/policies` | Historico de politicas clinicas. |
| `POST` | `/models/policies` | Criar nova politica clinica versionada com guardrails. |
| `POST` | `/models/policies/{id}/activate` | Ativar politica clinica com auditoria. |
| `GET` | `/governance/divergence` | Divergencia IA-humano por achado/modelo/politica, com filtros `from`, `to`, `model_version` e `clinical_policy_version`. |

## Endpoints Recomendados

| Metodo | Endpoint | Objetivo |
|---|---|---|
| `GET` | `/governance/incidents` | Falhas, bloqueios e violacoes de politica. |
| `GET` | `/models/versions/{id}/validation` | Evidencias, metricas e limitacoes do modelo. |

## Governanca Nirmata/Kyverno -> RX Clinico

| Governanca de infra | Governanca RX.AI |
|---|---|
| Policy-as-code | Politica clinica versionada. |
| Admission control | Bloqueio antes de inferencia/revisao/finalizacao. |
| Cluster policy | Regras por exame, achado, ambiente, papel e risco. |
| Artifact signing | Modelo versionado, model card, validacao e hash futuro. |
| Audit trail | Upload, de-id, predicao, politica, revisao e divergencia. |
| Multi-environment | `research -> validation -> pilot -> production`. |
| Deny non-compliant resource | Bloquear estudo sem de-id, modelo aprovado ou revisao humana. |

## Politicas Clinicas Minimas

1. `MandatoryHumanReview`: nenhum estudo finaliza sem revisao humana.
2. `DeIdentificationRequired`: DICOM nao persiste sem de-id.
3. `NoAutonomousDiagnosis`: IA nao emite laudo autonomo.
4. `CriticalFindingEscalation`: achado critico prioriza worklist.
5. `NoSilentPredictionOverwrite`: nova inferencia cria nova predicao.
6. `ModelVersionTraceability`: toda predicao referencia modelo usado.
7. `ClinicalPolicyTraceability`: predicao e revisao registram politica usada.
8. `ValidationEvidenceRequired`: modelo ativo precisa de model card/validacao
   antes de uso fora de pesquisa.

## Status de Politica Clinica

```text
draft -> active -> retired
```

- `draft`: politica criada para revisao, ainda sem uso operacional.
- `active`: politica vigente; somente uma deve estar ativa por vez.
- `retired`: politica historica preservada para auditoria e analise de
  divergencia.

Guardrails obrigatorios:

- `must_have_human_review=true`.
- `allow_autonomous_diagnosis=false`.
- `max_autoclose_without_review_minutes=0`.
- `allowed_workflow_states_for_auto_actions=[]`.
- `triage_priority_rules.critical_first=true`.
- `finalization_rules.allow_auto_finalize=false`.
- `disclaimer_rules.require_banner=true`.
- `disclaimer_rules.require_model_card_ack=true`.
- `audit_rules.log_policy_version_on_review=true`.
- `audit_rules.log_policy_version_on_divergence=true`.
- `human_review_required=true`.
- `autonomous_diagnosis_allowed=false`.
- `finalization_rule=blocked_until_human_review`.
- regras por achado nao podem desativar revisao humana.

## Papeis

| Papel | Permissao |
|---|---|
| `radiologist` | Revisar, corrigir/rejeitar IA e finalizar estudo. |
| `technician` | Upload e operacao sem finalizar revisao. |
| `admin_clinical` | Gerir politicas, usuarios, auditoria e filas. |
| `ml_engineer` | Registrar modelos e evidencias de validacao. |
| `qa_validator` | Validar modelos/politicas e registrar evidencias. |
| `auditor` | Ler auditoria, incidentes e divergencias. |
| `research_viewer` | Usar ambiente de pesquisa sem decisao clinica final. |

## Ordem de Implementacao Recomendada

1. Fortalecer politicas clinicas versionadas.
2. Criar mecanismo controlado para nova versao de politica.
3. Expandir auditoria de divergencia IA-humano.
4. Criar tela de governanca dedicada.
5. Separar ambientes `research`, `validation`, `production`.
6. So entao avaliar PACS/OHIF/Orthanc.
