"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api, ClinicalPolicy, DivergenceBucket, DivergenceReport, getToken, ModelVersion } from "../lib/api";

const findingLabels: Record<string, string> = {
  normal_no_critical_finding: "Sem achado critico",
  pneumothorax: "Pneumotorax",
  pleural_effusion: "Derrame pleural",
  consolidation: "Consolidacao",
  lung_opacity: "Opacidade pulmonar",
  cardiomegaly: "Cardiomegalia",
};

export default function GovernancePage() {
  const router = useRouter();
  const [report, setReport] = useState<DivergenceReport | null>(null);
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [policies, setPolicies] = useState<ClinicalPolicy[]>([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [modelVersion, setModelVersion] = useState("");
  const [policyVersion, setPolicyVersion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login?next=/governance");
      return;
    }
    setLoading(true);
    setError(null);
    Promise.all([
      api.divergenceReport({
        from: dateFrom ? `${dateFrom}T00:00:00` : undefined,
        to: dateTo ? `${dateTo}T23:59:59` : undefined,
        model_version: modelVersion || undefined,
        clinical_policy_version: policyVersion || undefined,
      }),
      api.modelVersions(),
      api.clinicalPolicies(),
    ])
      .then(([divergenceReport, modelRows, policyRows]) => {
        setReport(divergenceReport);
        setModels(modelRows);
        setPolicies(policyRows);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [dateFrom, dateTo, modelVersion, policyVersion, router]);

  const findingRows = useMemo(() => {
    return Object.entries(report?.by_finding || {})
      .map(([code, bucket]) => ({ code, ...bucket }))
      .sort((a, b) => b.divergences - a.divergences || b.reviewed_findings - a.reviewed_findings);
  }, [report]);

  const topFinding = findingRows.find((row) => row.divergences > 0);

  return (
    <div className="mx-auto max-w-7xl px-5 py-8">
      <div className="mb-7 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/" className="rx-kicker hover:text-white">Voltar para fila</Link>
          <h1 className="mt-2 max-w-4xl text-4xl font-black leading-[0.98] text-white md:text-6xl">
            Divergencia IA versus humano
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-7 text-[#b9d7e8] md:text-lg">
            Evidencia operacional para acompanhar onde a IA concorda com a revisao
            humana, onde diverge e quais achados exigem melhoria de modelo, politica
            ou validacao academica.
          </p>
        </div>
        <aside className="rx-panel-strong w-full p-5 sm:w-[340px]">
          <span className="rx-kicker text-[#ffb35c]">Uso governado</span>
          <dl className="mt-5 grid gap-4 text-sm">
            <div className="border-t border-white/15 pt-4">
              <dt className="font-black text-white">Fonte</dt>
              <dd className="mt-1 text-white/65">Revisoes humanas ja registradas.</dd>
            </div>
            <div className="border-t border-white/15 pt-4">
              <dt className="font-black text-white">Escopo</dt>
              <dd className="mt-1 text-white/65">Radiografia de torax no MVP.</dd>
            </div>
            <div className="border-t border-white/15 pt-4">
              <dt className="font-black text-white">Acao</dt>
              <dd className="mt-1 text-white/65">Auditar, validar e priorizar melhoria clinica.</dd>
            </div>
          </dl>
        </aside>
      </div>

      {error && <p className="rounded border border-critical/35 bg-critical/10 p-4 text-critical">{error}</p>}

      <section className="rx-panel mb-5 grid gap-4 p-4 md:grid-cols-[repeat(4,minmax(0,1fr))_auto] md:items-end">
        <div>
          <label htmlFor="governance-from" className="rx-label block">De</label>
          <input
            id="governance-from"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="rx-field mt-1 w-full px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="governance-to" className="rx-label block">Até</label>
          <input
            id="governance-to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="rx-field mt-1 w-full px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="governance-model" className="rx-label block">Modelo</label>
          <select
            id="governance-model"
            value={modelVersion}
            onChange={(e) => setModelVersion(e.target.value)}
            className="rx-field mt-1 w-full px-3 py-2 text-sm"
          >
            <option value="">Todos</option>
            {models.map((model) => (
              <option key={model.id} value={model.version}>{model.version}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="governance-policy" className="rx-label block">Política</label>
          <select
            id="governance-policy"
            value={policyVersion}
            onChange={(e) => setPolicyVersion(e.target.value)}
            className="rx-field mt-1 w-full px-3 py-2 text-sm"
          >
            <option value="">Todas</option>
            {policies.map((policy) => (
              <option key={policy.id} value={policy.version}>{policy.version}</option>
            ))}
            <option value="unknown_policy">Sem política registrada</option>
          </select>
        </div>
        <button
          type="button"
          onClick={() => {
            setDateFrom("");
            setDateTo("");
            setModelVersion("");
            setPolicyVersion("");
          }}
          className="min-h-[38px] rounded border border-white/10 px-3 py-2 text-xs font-black text-white/65 hover:bg-white/5 hover:text-white"
        >
          Limpar
        </button>
      </section>

      {loading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((item) => (
            <div key={item} className="rx-panel p-4">
              <div className="h-7 w-20 rounded bg-white/10" />
              <div className="mt-3 h-3 w-28 rounded bg-white/10" />
            </div>
          ))}
        </div>
      )}

      {!loading && report && (
        <>
          <section className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <GovernanceMetric value={report.summary.reviews} label="revisoes" />
            <GovernanceMetric value={report.summary.reviewed_findings} label="achados revisados" />
            <GovernanceMetric value={report.summary.divergences} label="divergencias" accent="text-[#ffb35c]" />
            <GovernanceMetric value={formatPercent(report.summary.divergence_rate)} label="taxa geral" accent="text-[#42e8ff]" />
            <GovernanceMetric value={report.summary.critical_divergences} label="divergencias criticas" accent="text-critical" />
          </section>

          <section className="rx-panel mb-5 p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <span className="rx-kicker">Leitura executiva</span>
                <h2 className="mt-2 text-xl font-black text-white">
                  {topFinding ? `${findingLabels[topFinding.code] || topFinding.code} concentra a maior divergencia` : "Sem divergencias registradas"}
                </h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-[#b9d7e8]">
                  A taxa vem de achados revisados por humanos contra a saida IA
                  persistida no momento da revisao. O indicador orienta validacao,
                  nao substitui revisao clinica.
                </p>
              </div>
              <Link href="/models" className="rounded border border-white/10 px-3 py-2 text-xs font-black text-white/65 hover:bg-[#86a8df]/10 hover:text-white">
                Ver modelos
              </Link>
            </div>
          </section>

          <section className="rx-panel mb-5 overflow-hidden">
            <div className="border-b border-white/10 px-5 py-4">
              <span className="rx-kicker">Por achado</span>
              <h2 className="mt-2 text-xl font-black text-white">Divergencia estruturada</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] border-collapse text-sm">
                <thead>
                  <tr className="bg-white/[0.035] text-left text-[0.66rem] uppercase tracking-[0.12em] text-white/42">
                    <th className="px-5 py-3">Achado</th>
                    <th className="px-5 py-3">Revisados</th>
                    <th className="px-5 py-3">Divergencias</th>
                    <th className="px-5 py-3">Taxa</th>
                    <th className="px-5 py-3">Sinal</th>
                  </tr>
                </thead>
                <tbody>
                  {findingRows.map((row) => (
                    <tr key={row.code} className="border-t border-white/10 text-white/75">
                      <td className="px-5 py-3 font-black text-white">{findingLabels[row.code] || row.code}</td>
                      <td className="px-5 py-3 text-[#b9d7e8]">{row.reviewed_findings}</td>
                      <td className="px-5 py-3 text-[#ffb35c]">{row.divergences}</td>
                      <td className="px-5 py-3">{formatPercent(row.divergence_rate)}</td>
                      <td className="px-5 py-3">
                        <DivergenceSignal bucket={row} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="grid gap-5 lg:grid-cols-2">
            <BreakdownCard title="Por decisao humana" rows={Object.entries(report.by_decision).map(([label, value]) => [label, String(value)])} />
            <BucketCard title="Por modelo" buckets={report.by_model_version} />
            <BucketCard title="Por politica clinica" buckets={report.by_clinical_policy} />
            <section className="rx-panel p-5">
              <span className="rx-kicker text-critical">Casos criticos</span>
              <h2 className="mt-2 text-xl font-black text-white">Pneumotorax divergente</h2>
              {report.critical_divergence_cases.length ? (
                <div className="mt-4 grid gap-3">
                  {report.critical_divergence_cases.map((item) => (
                    <Link key={item.review_id} href={`/studies/${item.study_id}`} className="rounded border border-critical/25 bg-critical/10 p-3 text-sm text-white/75 hover:bg-critical/15">
                      <strong className="block text-white">{item.decision}</strong>
                      <span className="mt-1 block text-xs text-white/50">{item.model_version} · {item.clinical_policy_version}</span>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="mt-4 text-sm leading-6 text-[#b9d7e8]">
                  Nenhuma divergencia critica registrada no banco atual.
                </p>
              )}
            </section>
          </div>
        </>
      )}
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

function DivergenceSignal({ bucket }: { bucket: DivergenceBucket }) {
  if (bucket.divergences === 0) {
    return <span className="rounded border border-[#6fa38f]/35 bg-[#6fa38f]/15 px-2 py-1 text-xs font-black text-[#8bc2ab]">estavel</span>;
  }
  if (bucket.divergence_rate >= 0.1) {
    return <span className="rounded border border-critical/30 bg-critical/15 px-2 py-1 text-xs font-black text-critical">revisar</span>;
  }
  return <span className="rounded border border-[#ffb35c]/30 bg-[#ffb35c]/10 px-2 py-1 text-xs font-black text-[#ffb35c]">monitorar</span>;
}

function BreakdownCard({ title, rows }: { title: string; rows: [string, string][] }) {
  return (
    <section className="rx-panel p-5">
      <span className="rx-kicker">{title}</span>
      <div className="mt-4 grid gap-3">
        {rows.length ? rows.map(([label, value]) => (
          <div key={label} className="flex items-center justify-between border-t border-white/10 pt-3 text-sm">
            <span className="font-bold text-white/70">{label}</span>
            <span className="font-black text-white">{value}</span>
          </div>
        )) : <p className="text-sm text-[#b9d7e8]">Sem dados revisados.</p>}
      </div>
    </section>
  );
}

function BucketCard({ title, buckets }: { title: string; buckets: Record<string, DivergenceBucket> }) {
  const rows = Object.entries(buckets);
  return (
    <section className="rx-panel p-5">
      <span className="rx-kicker">{title}</span>
      <div className="mt-4 grid gap-3">
        {rows.length ? rows.map(([label, bucket]) => (
          <div key={label} className="border-t border-white/10 pt-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="min-w-0 truncate font-bold text-white/70">{label}</span>
              <span className="font-black text-white">{formatPercent(bucket.divergence_rate)}</span>
            </div>
            <p className="mt-1 text-xs text-white/45">
              {bucket.divergences} divergencias em {bucket.reviewed_findings} achados
            </p>
          </div>
        )) : <p className="text-sm text-[#b9d7e8]">Sem dados revisados.</p>}
      </div>
    </section>
  );
}

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}
