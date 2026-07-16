# Hoje - DOD Rx

Este arquivo registra a acao pratica imediata do projeto. Ele deve ser usado
junto com `docs/CONTINUITY-WORKFLOW.md` e atualizado quando a etapa do dia
mudar.

## Decisao de hoje

Nao comecar por uma expansao tecnica grande. Primeiro consolidar o eixo do MVP:

- DOD Rx = leitura assistida de radiografia de torax.
- Visual = herdado do DOD ECG, sem alterar o ECG original.
- Saida IA = triagem e achados sugeridos.
- Revisao humana = obrigatoria antes de finalizacao.
- Governanca = auditoria, versao de modelo, decisao humana e seguranca clinica.

## Fluxo funcional inicial

1. Usuario cria ou acessa um estudo de torax.
2. Imagem e ingerida no fluxo do sistema.
3. Viewer exibe o estudo no navegador.
4. Servico de IA processa a radiografia.
5. IA devolve achados estruturados, probabilidades, prioridade e heatmaps quando
   disponiveis.
6. Usuario humano revisa, aceita, ajusta ou rejeita a saida.
7. Sistema grava auditoria, versao do modelo, revisor e decisao final.

## Arquitetura de referencia

Arquitetura atual do repo:

- Frontend: Next.js + Tailwind.
- Viewer: componente local `DicomViewer`, com caminho futuro para OHIF.
- Backend: FastAPI.
- ML: Python/PyTorch/TorchXRayVision ou mock.
- Banco: SQLite local/testes e PostgreSQL no caminho integrado.
- Auditoria: eventos persistidos por estudo.

Arquitetura alvo futura:

- Viewer radiologico: OHIF.
- Archive/PACS: Orthanc com DICOMweb.
- Backend clinico/IA: FastAPI.
- Banco relacional: PostgreSQL.
- Fila/cache: Redis ou equivalente.

## Acao pratica de hoje

A primeira passagem visual ja foi concluida e registrada em
`docs/HANDOFF.md`. A proxima etapa deve avancar governanca clinica sem quebrar
o fluxo existente.

1. Validar que `docs/HANDOFF.md` continua alinhado ao `AGENTS.md`.
2. Conferir o estado do dev local antes de qualquer nova implementacao.
3. Escolher a menor proxima mudanca concreta:
   - mecanismo controlado para criar nova versao de politica clinica; ou
   - mecanismo controlado para ativar uma politica clinica ja criada; ou
   - tela/relatorio de divergencia IA versus humano.
4. Preservar funcionamento atual de upload, predicao, revisao, auditoria,
   politica clinica versionada e historico de politicas.
5. Rodar verificacoes proporcionais:
   - testes backend se houver alteracao de API ou regra clinica;
   - build frontend se houver alteracao visual ou de cliente;
   - QA visual/API quando o fluxo clinico for tocado.

## Nao fazer hoje

- Nao mexer no DOD ECG.
- Nao implementar OHIF/Orthanc antes de fortalecer governanca clinica do MVP.
- Nao mudar o pipeline clinico sem necessidade.
- Nao remover disclaimers, auditoria ou revisao humana.
- Nao transformar a tela em landing page; a primeira tela deve ser ferramenta de
  trabalho.
