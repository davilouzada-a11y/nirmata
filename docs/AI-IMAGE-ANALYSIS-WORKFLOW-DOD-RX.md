# Fluxo IA + Imagem - DOD Rx / RX.AI

Este documento define a ordem operacional para imagem, comando de analise de IA,
heatmaps, revisao humana e auditoria.

## Ordem oficial

### 1. Upload da imagem

Entrada:

- DICOM (`.dcm`, `.dicom`);
- PNG;
- JPG/JPEG.

Regras:

- arquivo nao pode estar vazio;
- formato precisa ser suportado;
- DICOM deve ser desidentificado antes de persistir;
- upload cria estudo em `uploaded`;
- registrar auditoria `study.upload`;
- se DICOM, registrar `study.deidentify`.

### 2. Validacao tecnica da imagem

Validar:

- leitura possivel;
- formato suportado;
- dimensoes quando disponiveis;
- DICOM sem PHI persistido;
- caminho de storage criado;
- endpoint protegido por JWT.

Falhas devem bloquear o fluxo.

### 3. Criacao do estudo

Persistir:

- `Study`;
- `Patient` pseudonimizado/codificado;
- `image_format`;
- `image_path`;
- `view`;
- `status=uploaded`.

O frontend nao deve manipular estado clinico diretamente.

### 4. Comando de analise da IA

Endpoint:

```text
POST /studies/{id}/predict
```

Regras:

- estudo precisa existir;
- backend muda estado para `processing`;
- backend carrega modelo ativo;
- backend carrega thresholds do modelo;
- comando cria nova predicao; nunca sobrescreve anterior.

### 5. Resultado da IA

Persistir:

- `Prediction`;
- `PredictionFinding`;
- probabilidades;
- thresholds aplicados;
- `overall_status`;
- heatmaps quando disponiveis;
- latencia;
- `model_version`.

Auditoria:

- `study.predict`;
- payload deve conter `prediction_id`, `overall_status` e `model_version`.

### 6. Exibicao da imagem

Viewer:

- PNG/JPG via imagem autenticada;
- DICOM via DWV local;
- heatmap como overlay opcional;
- brilho/contraste podem ser ajustados no cliente.
- acesso a imagem registra auditoria `image.viewed`;
- acesso a heatmap registra auditoria `image.heatmap_viewed`.

Limites:

- heatmap e apoio visual, nao prova diagnostica;
- probabilidade e apoio de triagem, nao laudo;
- viewer atual e MVP; OHIF fica para etapa futura.

### 7. Revisao humana

Endpoint:

```text
POST /studies/{id}/review
```

Regras:

- revisao exige predicao existente;
- medico confirma, corrige ou rejeita IA;
- bloqueios de revisao registram `policy.denied`;
- revisao permitida registra `policy.evaluated`;
- sistema registra achado final por classe;
- sistema registra divergencia IA-humano por achado;
- sistema permite comentario por achado;
- sistema registra `clinical_policy_version`;
- estudo so finaliza apos revisao humana.

Auditoria:

- `study.review`;
- payload deve conter `review_id`, `decision`, `prediction_id`,
  `model_version_id`, `clinical_policy_version` e divergencias.

### 8. Finalizacao

Estado final:

```text
finalized
```

Somente permitido quando:

- ha predicao registrada;
- ha revisao humana registrada;
- ha politica clinica versionada;
- ha auditoria do fluxo.

## Comandos principais

### Upload

```bash
curl -X POST http://127.0.0.1:8000/studies/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "patient_code=P-001" \
  -F "view=PA" \
  -F "file=@/path/to/image.dcm"
```

### Inferencia

```bash
curl -X POST http://127.0.0.1:8000/studies/$STUDY_ID/predict \
  -H "Authorization: Bearer $TOKEN"
```

### Revisao

```bash
curl -X POST http://127.0.0.1:8000/studies/$STUDY_ID/review \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"decision":"confirmed","prediction_id":"...","final_report":"...","final_findings":[]}'
```

## Auditoria minima por estudo

Fluxo ideal:

```text
study.upload
study.deidentify        # quando DICOM
image.viewed
study.predict
policy.evaluated
study.review
study.hold
study.reopened
```

Eventos futuros recomendados:

```text
policy.evaluated
policy.denied
prediction.failed
review.opened
divergence.detected
```

## Principio de seguranca

Se faltar imagem valida, modelo versionado, politica clinica ativa, auditoria ou
revisao humana, o sistema deve bloquear a finalizacao.
