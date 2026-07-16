# Validacao DICOM Local - DOD Rx

Este roteiro prova o eixo tecnico atual do MVP sem depender de PACS, Orthanc ou
OHIF. Ele usa apenas DICOM sintetico com PHI falsa.

## Objetivo

Validar que um estudo DICOM local consegue atravessar o fluxo essencial:

1. gerar DICOM sintetico com metadados identificaveis falsos;
2. desidentificar antes de persistir;
3. gravar estudo no backend;
4. exibir o arquivo protegido pelo endpoint autenticado;
5. rodar inferencia;
6. exigir revisao humana;
7. registrar auditoria.

## Comandos principais

Na pasta `backend`:

```bash
cd backend
. .venv/bin/activate
pytest -q
```

O teste `test_dicom_upload_is_deidentified_on_disk` cobre o caminho DICOM mais
importante:

- o arquivo original contem PHI falsa (`PatientName`, `PatientID`,
  `InstitutionName`, `DeviceSerialNumber` e tag privada);
- o upload so persiste o DICOM depois de `process_dicom`;
- o arquivo servido por `/studies/{id}/image` ja esta desidentificado;
- a trilha de auditoria registra `study.deidentify`.

## Gerar um DICOM sintetico manualmente

Na raiz do repositorio, usando o venv do backend:

```bash
. backend/.venv/bin/activate
python -m ml.preprocessing --make-sample /tmp/dod-rx-sample.dcm
```

Esse arquivo e somente para desenvolvimento. Ele contem PHI falsa para exercitar
o processo de limpeza.

## Rodar preprocessamento manual

```bash
. backend/.venv/bin/activate
python -m ml.preprocessing \
  --in /tmp/dod-rx-sample.dcm \
  --out-dir /tmp/dod-rx-preprocessed \
  --salt local-dev
```

Saidas esperadas:

- PNG de exibicao;
- DICOM desidentificado;
- JSON/manifesto de limpeza;
- `PatientIdentityRemoved=YES` no DICOM resultante.

## Criterios de aceite

- Nenhum DICOM bruto com PHI deve tocar `backend/storage`.
- Upload DICOM corrompido deve retornar `422`.
- Upload DICOM valido deve retornar `201`.
- O estudo criado deve manter `image_format=dicom`.
- `width` e `height` devem ser preenchidos quando o DICOM puder ser lido.
- Auditoria deve conter `study.upload` e `study.deidentify`.
- Inferencia nao deve sobrescrever predicoes antigas.
- Finalizacao clinica continua exigindo revisao humana.

## Limites conhecidos

- O viewer atual usa DWV local; OHIF continua como alvo futuro.
- O fluxo local valida ingestao e seguranca basica, nao substitui validacao com
  PACS real.
- A desidentificacao de metadados nao remove texto queimado nos pixels; quando
  `BurnedInAnnotation=YES`, o pipeline sinaliza necessidade de revisao/OCR.
