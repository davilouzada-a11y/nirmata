# Arquitetura - DOD Rx

## Resumo

DOD Rx combina uma aplicacao web, uma API clinica, um pipeline de inferencia e
uma camada de auditoria para leitura assistida de radiografias.

Arquitetura atual:

```text
Next.js frontend
  -> FastAPI backend
    -> ML bridge / inference backend
      -> mock, TorchXRayVision ou checkpoint proprio
    -> banco relacional
    -> armazenamento local/objeto para imagens e derivados
```

Arquitetura alvo quando houver integracao PACS:

```text
Next.js shell DOD Rx
  -> OHIF Viewer
    -> Orthanc + DICOMweb
  -> FastAPI backend
    -> fila async
    -> servico IA
    -> PostgreSQL
    -> object storage
    -> auditoria/governanca
```

## Frontend

Base atual:

- `frontend/app/page.tsx`: home/worklist/upload.
- `frontend/app/studies/[id]/page.tsx`: detalhe do estudo.
- `frontend/app/components/DicomViewer.tsx`: visualizacao de DICOM/imagens e
  heatmap.
- `frontend/app/components/FindingList.tsx`: achados da IA.
- `frontend/app/components/ReviewForm.tsx`: revisao humana.
- `frontend/app/components/AuditTimeline.tsx`: eventos.
- `frontend/app/components/StatsPanel.tsx`: metricas.
- `frontend/app/models/page.tsx`: registro de modelos.

Direcao visual:

- evoluir o shell para ficar mais proximo do DOD ECG;
- manter densidade profissional, dark mode, cards executivos e worklist clara;
- evitar layout de landing page;
- priorizar tela util de trabalho desde o primeiro viewport.

## Backend

Base atual:

- `backend/app/main.py`: aplicacao FastAPI.
- `backend/app/api/studies.py`: upload, fila, predicao, review e imagens.
- `backend/app/api/auth.py`: autenticacao.
- `backend/app/api/audit.py`: trilha de auditoria.
- `backend/app/api/models.py`: versoes de modelo.
- `backend/app/services/study_service.py`: orquestracao de estudos.
- `backend/app/services/inference_service.py`: inferencia.
- `backend/app/services/review_service.py`: revisao.
- `backend/app/services/audit_service.py`: eventos.

Regras:

- manter backend como fonte de verdade do workflow;
- bloquear finalizacao sem revisao humana;
- registrar toda acao clinicamente relevante;
- versionar modelo e preservar historico de predicoes.

## ML

Base atual:

- `ml/inference/`: preprocessamento, preditores e Grad-CAM.
- `ml/preprocessing/`: desidentificacao e transformacoes DICOM.
- `ml/training/`: treino/evaluate.
- `ml/validation/`: validacao, calibracao e relatorios.

Findings do MVP documentados no README e modelo:

- `normal_no_critical_finding`
- `pneumothorax`
- `pleural_effusion`
- `consolidation`
- `cardiomegaly`
- `lung_opacity` quando habilitado pela validacao.

## Viewer e PACS

Estado atual:

- o viewer local atende o MVP e permite iterar o produto sem depender de PACS;
- imagens DICOM/PNG/JPG podem ser usadas no fluxo atual.

Alvo futuro:

- Orthanc para archive/PACS;
- DICOMweb para acesso padronizado;
- OHIF para viewer radiologico completo;
- FastAPI continua como camada clinica, governanca e integracao de IA.

## Governanca inspirada no Nirmata

A inspiracao do Nirmata nao e copiar produto de infraestrutura. A ideia e
aplicar governanca forte ao dominio radiologico:

- regras por protocolo, modalidade, projecao e qualidade;
- thresholds versionados;
- modelos versionados;
- bloqueios para baixa confianca;
- revisao obrigatoria para achados criticos;
- auditoria de quem viu, revisou, aceitou, rejeitou e finalizou.

Exemplos de politica:

- Exame AP portatil pode receber triagem, mas nao laudo automatico.
- Confianca abaixo do limiar marca `needs_human_review`.
- Pneumotorax positivo sobe prioridade da worklist.
- Toda inferencia registra modelo, versao, timestamp e usuario revisor posterior.

## Integracoes futuras

- Orthanc/DICOMweb.
- OHIF embutido ou integrado por rota.
- Fila async com Redis/Celery/RQ quando inferencia deixar de ser imediata.
- Object storage para imagens, heatmaps e derivados.
- RBAC mais granular por perfil clinico/admin.
- Ambiente separado para pesquisa, validacao e producao.
