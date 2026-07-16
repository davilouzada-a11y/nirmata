# Politica Medico-Etica, Legal e Academica - DOD Rx

Este documento define a base etica, legal, academica e operacional do DOD Rx.
Ele orienta a implementacao tecnica, mas nao substitui parecer juridico,
avaliacao regulatoria, comite de etica, validacao clinica ou responsabilidade
do medico habilitado.

## Principio central

DOD Rx e uma ferramenta de apoio a decisao em radiografia de torax. A IA nao
emite diagnostico autonomo, nao substitui o medico e nao finaliza estudo sem
revisao humana registrada.

Toda politica computacional deve preservar:

- autonomia e dignidade do paciente;
- beneficencia;
- nao maleficencia;
- justica e equidade;
- sigilo e privacidade;
- rastreabilidade;
- responsabilidade profissional humana;
- transparencia cientifica sobre limites, dados e desempenho.

## Escopo atual

- Modalidade inicial: radiografia de torax.
- Saida da IA: triagem e achados sugeridos.
- Uso inicial: pesquisa, desenvolvimento, ensino e avaliacao controlada.
- Decisao clinica final: obrigatoriamente humana.
- Finalizacao: bloqueada ate revisao humana registrada.

## Regras medico-eticas

- IA e sempre advisory.
- A decisao clinica final pertence ao medico revisor.
- Nenhum resultado deve ser apresentado como laudo autonomo da IA.
- Achados criticos devem priorizar atencao humana, nao automatizar conduta.
- Divergencias entre IA e humano devem ser registradas, nao apagadas.
- O sistema deve favorecer prudencia, revisao e explicabilidade.
- O sistema nao deve ser desenhado para induzir excesso de confianca na IA.
- Heatmaps e probabilidades sao apoio interpretativo, nao prova diagnostica.

## Regras legais e de privacidade

- Dados de saude devem ser tratados como dados pessoais sensiveis.
- DICOM deve ser desidentificado antes de persistencia sempre que possivel.
- Acesso, upload, inferencia, revisao e decisoes relevantes devem ser auditados.
- O projeto deve minimizar coleta, retencao e exposicao de dados pessoais.
- Qualquer uso real fora de ambiente controlado deve exigir avaliacao juridica,
  regulatoria e institucional.
- Bases legais, consentimento, compartilhamento e responsabilidade devem ser
  definidos antes de uso clinico ou institucional.
- O sistema deve preservar sigilo medico e controle de acesso.

## Regras academicas e cientificas

- Modelos devem ter versao, origem, dataset quando disponivel e thresholds
  registrados.
- Politicas clinicas devem ser versionadas separadamente do modelo.
- Validacao deve reportar metricas por achado, populacao, limitacoes e vieses.
- O uso academico deve distinguir claramente demonstracao, pesquisa, validacao e
  uso clinico.
- Estudos com dados reais devem seguir as regras institucionais aplicaveis,
  incluindo comite de etica quando necessario.
- Resultados nao validados nao devem ser comunicados como desempenho clinico.
- Mudancas de modelo ou politica devem preservar historico e rastreabilidade.

## Regras computacionais obrigatorias

- Registrar `model_version` em toda predicao.
- Registrar `clinical_policy_version` em toda revisao/finalizacao humana.
- Criar nova predicao ao reprocessar; nunca sobrescrever predicao antiga.
- Registrar usuario revisor, decisao, achados finais, divergencias e comentarios.
- Bloquear finalizacao sem revisao humana.
- Priorizar worklist quando politica ativa definir achado critico.
- Exibir disclaimers de apoio a decisao e revisao humana obrigatoria.
- Nao remover auditoria, disclaimers ou barreiras de seguranca para acelerar a
  experiencia.

## Politica clinica versionada atual

Versao inicial:

```text
dod-rx-cxr-policy-v0.1.0
```

Escopo:

- radiografia de torax MVP;
- triagem e achados sugeridos;
- revisao humana obrigatoria;
- diagnostico autonomo nao permitido;
- finalizacao bloqueada ate revisao humana;
- pneumotorax como achado critico inicial que prioriza worklist.

## Criterio de evolucao

Uma nova politica clinica deve ser criada quando houver mudanca em qualquer um
destes itens:

- achados criticos;
- regra de prioridade;
- regra de revisao humana;
- regra de finalizacao;
- escopo de exame;
- populacao alvo;
- uso pretendido;
- criterio academico/regulatorio;
- limite etico ou legal relevante.

Cada nova politica deve receber nova versao, preservar a anterior e registrar o
motivo da mudanca.

## Fora de escopo sem nova avaliacao

- Diagnostico autonomo.
- Prescricao automatizada.
- Substituicao de laudo medico.
- Uso clinico institucional sem validacao, governanca e avaliacao regulatoria.
- Compartilhamento de dados identificaveis sem base legal definida.
- Uso em exames fora do escopo sem nova politica e validacao.
