# Arquitetura Clinica de Imagem - DOD Rx / RX.AI

Este documento define o desenho textual da arquitetura clinica de analise de
imagem do DOD Rx. O objetivo e manter separacao total entre imagem, IA,
decisao medica, politica clinica e governanca.

## Principio cirurgico

Nao existe caminho direto de imagem para laudo.

```text
Imagem -> IA advisory -> revisao humana -> finalizacao auditada
```

A IA observa e sugere. A politica clinica controla o uso. O medico decide. A
auditoria registra.

## Desenho textual atual

```text
Frontend Next.js
  -> Worklist / upload / viewer / achados / revisao / governanca
  -> usa JWT para acessar a API

Backend FastAPI
  -> autentica usuario
  -> controla workflow clinico
  -> serve imagem por endpoint protegido
  -> chama servico de inferencia
  -> persiste predicoes, revisoes, politicas e auditoria

Servico de ML
  -> recebe imagem preparada
  -> executa modelo versionado
  -> devolve achados, scores, overall_status, latencia e heatmaps
  -> nao decide clinicamente

Storage de imagem/DICOM
  -> guarda DICOM desidentificado, PNG/JPG e derivados
  -> nunca e acessado diretamente pelo viewer
  -> acesso sempre passa pelo backend

Banco relacional
  -> estudos, pacientes pseudonimizados, modelo, predicao, revisao,
     politica clinica e auditoria
```

## Camada de imagem

Entrada permitida:

- DICOM (`.dcm`, `.dicom`);
- PNG;
- JPG/JPEG.

Fluxo:

```text
upload -> validacao tecnica -> de-identificacao DICOM -> storage seguro
       -> Study(status=uploaded) -> auditoria
```

Regras:

- DICOM deve ser desidentificado antes de persistir.
- O frontend nao fala diretamente com storage.
- O viewer acessa imagens apenas por endpoints protegidos.
- Imagem e DICOM sao dados sensiveis, nao assets publicos.

Endpoints atuais:

```text
POST /studies/upload
GET  /studies/{id}/image
GET  /studies/{id}/heatmaps/{finding_code}
```

Alvo futuro, quando PACS justificar:

```text
OHIF Viewer -> DICOMweb -> Orthanc/PACS
FastAPI continua como camada clinica, politica e auditoria
```

## Camada de IA de imagem

Endpoint:

```text
POST /studies/{id}/predict
```

Responsabilidade unica:

```text
pegar imagem preparada
-> carregar modelo/thresholds
-> rodar inferencia
-> salvar Prediction e PredictionFinding
-> gerar heatmaps quando disponiveis
-> devolver achados e probabilidades
```

A IA pode devolver:

- `model_version`;
- `overall_status`;
- achados estruturados;
- probabilidades;
- thresholds aplicados;
- heatmaps;
- latencia de inferencia.

A IA nao pode devolver:

- diagnostico autonomo;
- laudo final;
- conduta;
- finalizacao;
- ordem clinica automatica.

## Camada de decisao clinica

Endpoint:

```text
POST /studies/{id}/review
```

Este e o unico ponto em que ocorre decisao clinica.

Fluxo:

```text
Prediction disponivel
-> medico revisa
-> compara "IA sugeriu" versus "medico decidiu"
-> registra decisao por achado
-> registra divergencias e comentarios
-> aplica clinical_policy ativa
-> finaliza estudo
-> auditoria
```

Regras:

- Revisao humana e obrigatoria.
- Finalizacao sem revisao humana e bloqueada.
- Divergencia IA-humano deve ser persistida, nao apagada.
- `clinical_policy_version` pertence ao eixo de revisao/finalizacao, nao ao
  motor de inferencia.
- Texto clinico final vem do humano.

## Camada de politica clinica

Entidade:

```text
ClinicalPolicy
```

Papel:

```text
modelo = motor
politica = freio + regra de uso + governanca
```

A politica clinica define:

- revisao humana obrigatoria;
- bloqueio de diagnostico autonomo;
- achados criticos que exigem atencao humana;
- regra de prioridade da worklist;
- regra de finalizacao;
- banner/disclaimer obrigatorio;
- auditoria de revisao e divergencia;
- quem pode criar/ativar politica;
- status `draft`, `active`, `retired`.

Endpoints:

```text
GET  /models/policy/active
GET  /models/policies
POST /models/policies
POST /models/policies/{id}/activate
```

Guardrails minimos:

```text
must_have_human_review=true
allow_autonomous_diagnosis=false
max_autoclose_without_review_minutes=0
allowed_workflow_states_for_auto_actions=[]
finalization_rules.allow_auto_finalize=false
disclaimer_rules.require_banner=true
audit_rules.log_policy_version_on_review=true
audit_rules.log_policy_version_on_divergence=true
```

## Camada de governanca

Endpoint:

```text
GET /governance/divergence
```

Filtros:

```text
from
to
model_version
clinical_policy_version
```

O relatorio cruza:

- achado;
- modelo;
- politica clinica;
- decisao humana;
- divergencia IA-humano;
- casos criticos.

Objetivo:

```text
avaliar uso da IA sem alterar silenciosamente o motor
```

## Caminhos proibidos

```text
Imagem -> laudo
Imagem -> finalizacao
IA -> laudo
IA -> finalizacao
Viewer -> storage direto
Frontend -> alterar estado clinico diretamente
Politica -> permitir diagnostico autonomo
Politica -> remover revisao humana
Predicao -> sobrescrever predicao anterior
```

## Caminhos permitidos

```text
Imagem -> storage protegido
Imagem -> viewer autenticado
Imagem -> IA advisory
IA advisory -> revisao humana
Revisao humana -> finalizacao
Politica ativa -> regra de revisao/finalizacao
Auditoria -> trilha de upload, de-id, predicao, revisao e politica
Governanca -> analise de divergencia por achado/modelo/politica
```

## Auditoria minima

Eventos atuais:

```text
study.upload
study.deidentify
image.viewed
image.heatmap_viewed
study.predict
policy.denied
policy.evaluated
study.review
policy.create
policy.activate
study.hold
study.reopened
```

Eventos recomendados:

```text
review.opened
prediction.failed
divergence.detected
```

## Regra final

Se faltar qualquer item abaixo, o sistema deve bloquear finalizacao:

- imagem valida;
- estudo persistido;
- predicao versionada;
- politica clinica ativa;
- revisao humana;
- auditoria do fluxo.
