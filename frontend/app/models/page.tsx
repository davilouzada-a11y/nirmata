"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, getToken, ClinicalPolicy, ModelVersion } from "../lib/api";

export default function ModelsPage() {
  const router = useRouter();
  const [versions, setVersions] = useState<ModelVersion[]>([]);
  const [policy, setPolicy] = useState<ClinicalPolicy | null>(null);
  const [policies, setPolicies] = useState<ClinicalPolicy[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) { router.replace("/login?next=/models"); return; }
    setLoading(true);
    setError(null);
    Promise.all([api.modelVersions(), api.activePolicy(), api.clinicalPolicies()])
      .then(([modelVersions, activePolicy, policyHistory]) => {
        setVersions(modelVersions);
        setPolicy(activePolicy);
        setPolicies(policyHistory);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [router]);

  const activeModel = versions[0];
  const totalThresholds = activeModel ? Object.keys(activeModel.threshold_config || {}).length : 0;
  const criticalThresholds = policy?.critical_findings.length || 0;
  const rulesByFinding = Object.fromEntries((policy?.rules || []).map((rule) => [rule.finding_code, rule]));
  const disclaimerRules = (policy?.rule_guardrails?.disclaimer_rules || {}) as { banner_text?: string };

  return (
    <div className="mx-auto max-w-7xl px-5 py-8">
      <div className="mb-7 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/" className="rx-kicker hover:text-white">Voltar para fila</Link>
          <h1 className="mt-2 max-w-4xl text-4xl font-black leading-[0.98] text-white md:text-6xl">
            Governanca de modelos
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-7 text-[#b9d7e8] md:text-lg">
            Cada predicao referencia a versao exata do modelo, thresholds e dataset
            de treinamento quando disponivel. Esta tela sustenta rastreabilidade,
            auditoria e revisao humana.
          </p>
        </div>
        <aside className="rx-panel-strong w-full p-5 sm:w-[340px]">
          <span className="rx-kicker text-[#ffb35c]">Politica ativa</span>
          <dl className="mt-5 grid gap-4 text-sm">
            <div className="border-t border-white/15 pt-4">
              <dt className="font-black text-white">Saida clinica</dt>
              <dd className="mt-1 text-white/65">Triagem e achados sugeridos.</dd>
            </div>
            <div className="border-t border-white/15 pt-4">
              <dt className="font-black text-white">Aceite final</dt>
              <dd className="mt-1 text-white/65">Somente apos revisao humana.</dd>
            </div>
            <div className="border-t border-white/15 pt-4">
              <dt className="font-black text-white">Achado critico</dt>
              <dd className="mt-1 text-white/65">
                {policy?.critical_findings.join(", ") || "Regra nao carregada"} prioriza a worklist.
              </dd>
            </div>
            <div className="border-t border-white/15 pt-4">
              <dt className="font-black text-white">Politica</dt>
              <dd className="mt-1 text-white/65">{policy?.version || "Carregando politica..."}</dd>
            </div>
          </dl>
        </aside>
      </div>

      {error && <p className="rounded border border-critical/35 bg-critical/10 p-4 text-critical">{error}</p>}

      {loading && (
        <div className="grid gap-4 lg:grid-cols-2">
          {[0, 1].map((item) => (
            <div key={item} className="rx-panel p-5">
              <div className="h-4 w-24 rounded bg-white/10" />
              <div className="mt-4 h-7 w-64 rounded bg-white/10" />
              <div className="mt-5 grid gap-2">
                {[0, 1, 2, 3].map((row) => (
                  <div key={row} className="h-10 rounded bg-white/[0.06]" />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && activeModel && (
        <section className="mb-5 grid gap-3 sm:grid-cols-3">
          <GovernanceMetric value={activeModel.version} label="modelo ativo" />
          <GovernanceMetric value={totalThresholds} label="thresholds versionados" accent="text-[#42e8ff]" />
          <GovernanceMetric value={criticalThresholds} label="regras clínicas críticas" accent="text-critical" />
        </section>
      )}

      {!loading && policy && (
        <section className="rx-panel mb-5 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <span className="rx-kicker text-[#ffb35c]">Politica clinica versionada</span>
              <h2 className="mt-2 text-xl font-black text-white">{policy.version}</h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-[#b9d7e8]">
                Escopo {policy.scope}; saida {policy.clinical_output}; finalizacao
                bloqueada ate revisao humana.
              </p>
              <p className="mt-3 max-w-3xl rounded border border-[#ffb35c]/25 bg-[#ffb35c]/10 p-3 text-sm leading-6 text-[#ffd4a0]">
                {disclaimerRules.banner_text || "Apoio a decisao em radiografia de torax. Nao e dispositivo diagnostico. Uso assistencial exige validacao clinica e regularizacao."}
              </p>
            </div>
            <span className="rounded border border-[#6fa38f]/35 bg-[#6fa38f]/15 px-3 py-2 text-xs font-black text-[#8bc2ab]">
              HITL obrigatorio
            </span>
          </div>
        </section>
      )}

      {!loading && policies.length > 0 && (
        <section className="rx-panel mb-5 overflow-hidden">
          <div className="border-b border-white/10 px-5 py-4">
            <span className="rx-kicker">Historico de politicas clinicas</span>
            <h2 className="mt-2 text-xl font-black text-white">Versoes e estado</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] border-collapse text-sm">
              <thead>
                <tr className="bg-white/[0.035] text-left text-[0.66rem] uppercase tracking-[0.12em] text-white/42">
                  <th className="px-5 py-3">Politica</th>
                  <th className="px-5 py-3">Escopo</th>
                  <th className="px-5 py-3">Regras</th>
                  <th className="px-5 py-3">Criticas</th>
                  <th className="px-5 py-3">Estado</th>
                  <th className="px-5 py-3">Criada em</th>
                </tr>
              </thead>
              <tbody>
                {policies.map((item) => (
                  <tr key={item.id} className="border-t border-white/10 text-white/75">
                    <td className="px-5 py-3">
                      <div className="font-black text-white">{item.version}</div>
                      <div className="mt-1 text-xs text-white/42">{item.name}</div>
                    </td>
                    <td className="px-5 py-3">{item.scope}</td>
                    <td className="px-5 py-3 text-[#b9d7e8]">{item.rules.length}</td>
                    <td className="px-5 py-3 text-critical">{item.critical_findings.length}</td>
                    <td className="px-5 py-3">
                      {item.status === "active" ? (
                        <span className="rounded border border-[#6fa38f]/35 bg-[#6fa38f]/15 px-2 py-1 text-xs font-black text-[#8bc2ab]">
                          ativa
                        </span>
                      ) : item.status === "draft" ? (
                        <span className="rounded border border-[#ffb35c]/30 bg-[#ffb35c]/10 px-2 py-1 text-xs font-black text-[#ffb35c]">
                          draft
                        </span>
                      ) : (
                        <span className="text-xs font-bold text-white/42">{item.status}</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-white/50">{new Date(item.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {!loading && versions.map((m, index) => (
          <article key={m.id} className="rx-panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="rx-kicker">{index === 0 ? "Modelo ativo" : "Modelo registrado"}</span>
                <h2 className="mt-2 text-xl font-black text-white">{m.version}</h2>
              </div>
              <div className="flex flex-col items-end gap-2">
                {index === 0 && (
                  <span className="rounded border border-[#6fa38f]/35 bg-[#6fa38f]/15 px-2 py-1 text-xs font-black text-[#8bc2ab]">
                    em uso
                  </span>
                )}
                <span className="rounded border border-white/10 px-2 py-1 text-xs font-bold text-white/45">
                  {new Date(m.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
            <p className="mt-3 text-sm font-bold text-[#b9d7e8]">{m.name}</p>
            {m.training_dataset && (
              <p className="mt-2 text-xs text-white/45">Dataset: {m.training_dataset}</p>
            )}
            <div className="mt-4 border-t border-white/10 pt-4">
              <span className="text-[0.7rem] font-extrabold uppercase tracking-[0.12em] text-white/45">Thresholds e regras</span>
              <div className="mt-3 overflow-hidden rounded border border-white/10">
                <table className="w-full border-collapse text-sm">
                  <thead className="bg-white/[0.035] text-left text-[0.66rem] uppercase tracking-[0.12em] text-white/42">
                    <tr>
                      <th className="px-3 py-2">Achado</th>
                      <th className="px-3 py-2">Limiar</th>
                      <th className="px-3 py-2">Regra</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(m.threshold_config || {}).map(([code, thr]) => {
                      const rule = rulesByFinding[code];
                      const critical = Boolean(rule?.critical);
                      return (
                        <tr key={code} className="border-t border-white/10 text-white/75">
                          <td className="px-3 py-2 font-bold">{rule?.label || code}</td>
                          <td className="px-3 py-2 text-[#b9d7e8]">{Math.round(Number(thr) * 100)}%</td>
                          <td className="px-3 py-2">
                            {critical ? (
                              <span className="rounded border border-critical/30 bg-critical/15 px-2 py-1 text-[11px] font-black text-critical">
                                prioriza
                              </span>
                            ) : (
                              <span className="text-xs font-bold text-white/42">triagem</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </article>
        ))}
        {!loading && !versions.length && !error && (
          <p className="rx-panel p-5 text-[#b9d7e8]">Nenhum modelo registrado.</p>
        )}
      </div>
    </div>
  );
}

function GovernanceMetric({ value, label, accent }: { value: string | number; label: string; accent?: string }) {
  return (
    <div className="rx-panel px-4 py-3">
      <div className={`truncate text-2xl font-black leading-none ${accent || "text-white"}`}>{value}</div>
      <div className="mt-2 text-[0.7rem] font-extrabold uppercase tracking-[0.12em] text-white/50">{label}</div>
    </div>
  );
}
