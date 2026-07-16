"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, getToken, Prediction } from "../../lib/api";
import DicomViewer from "../../components/DicomViewer";
import FindingList from "../../components/FindingList";
import HeatmapOverlayToggle from "../../components/HeatmapOverlayToggle";
import ReviewForm from "../../components/ReviewForm";
import AuditTimeline from "../../components/AuditTimeline";

export default function StudyPage() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();

  const [study, setStudy] = useState<any>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [review, setReview] = useState<any>(null);
  const [selectedFinding, setSelectedFinding] = useState<string | null>(null);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [opacity, setOpacity] = useState(0.55);
  const [auditKey, setAuditKey] = useState(0);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const s = await api.getStudy(id);
    setStudy(s);

    if (["predicted", "under_review", "reviewed", "finalized"].includes(s.status)) {
      try { setPrediction(await api.getPrediction(id)); } catch { setPrediction(null); }
    } else {
      setPrediction(null);
    }

    if (["reviewed", "finalized"].includes(s.status)) {
      try { setReview(await api.getReview(id)); } catch { setReview(null); }
    } else {
      setReview(null);
    }
  }, [id]);

  useEffect(() => {
    if (!getToken()) { router.replace(`/login?next=/studies/${id}`); return; }
    load();
  }, [id, load, router]);

  async function runPrediction() {
    setBusy(true);
    try {
      setPrediction(await api.predict(id));
      setAuditKey((k) => k + 1);
      await load();
    } catch (err) {
      alert((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function submitReview(payload: any) {
    await api.submitReview(id, payload);
    setAuditKey((k) => k + 1);
    await load();
  }

  if (!study) return <p className="p-6 text-slate-400">Carregando…</p>;

  const selected = prediction?.findings.find((f) => f.finding_code === selectedFinding);
  const heatmapUrl = selected?.heatmap_url ? api.heatmapUrl(id, selected.finding_code) : null;

  const overallBadge =
    prediction?.overall_status === "abnormal_critical"
      ? "border-critical/35 bg-critical/15 text-critical"
      : prediction?.overall_status === "abnormal_noncritical"
      ? "border-[#ffb35c]/35 bg-[#ffb35c]/10 text-[#ffb35c]"
      : "border-[#6fa38f]/35 bg-[#6fa38f]/15 text-[#8bc2ab]";

  return (
    <div className="mx-auto max-w-7xl px-5 py-8">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/" className="rx-kicker hover:text-white">Voltar para fila</Link>
          <h1 className="mt-2 text-3xl font-black leading-tight text-white md:text-5xl">
            Paciente {study.patient_code}
          </h1>
          <div className="mt-3 flex flex-wrap gap-2 text-xs font-black uppercase tracking-[0.12em] text-white/55">
            <span className="rounded border border-white/10 bg-white/5 px-2 py-1">{study.view}</span>
            <span className="rounded border border-white/10 bg-white/5 px-2 py-1">{study.status}</span>
            <span className="rounded border border-white/10 bg-white/5 px-2 py-1">
              {study.image_format || "imagem"}
            </span>
          </div>
        </div>
        {prediction && (
          <span className={`rounded border px-3 py-2 text-xs font-black ${overallBadge}`}>
            {prediction.overall_status} · {prediction.model_version}
          </span>
        )}
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* AI findings */}
        <aside className="rx-panel col-span-12 space-y-4 p-4 lg:col-span-3">
          <div>
            <span className="rx-kicker">Inferencia</span>
            <h2 className="mt-1 text-lg font-black text-white">Achados da IA</h2>
          </div>
          {prediction ? (
            <FindingList
              findings={prediction.findings}
              selected={selectedFinding}
              onSelect={setSelectedFinding}
            />
          ) : (
            <button onClick={runPrediction} disabled={busy}
              className="w-full rounded bg-white py-3 text-sm font-black text-[#07090d] transition hover:-translate-y-0.5 hover:bg-white/90 disabled:opacity-50">
              {busy ? "Processando…" : "Rodar análise da IA"}
            </button>
          )}
          {prediction && (
            <p className="border-t border-white/10 pt-3 text-[11px] leading-5 text-white/45">{prediction.disclaimer}</p>
          )}
        </aside>

        {/* Viewer */}
        <section className="col-span-12 space-y-3 lg:col-span-6">
          <div className="rx-panel-strong p-3">
            <div className="mb-3 flex items-center justify-between gap-3 border-b border-white/10 pb-3">
              <div>
                <span className="rx-kicker">Viewer radiologico</span>
                <p className="mt-1 text-xs text-white/50">Imagem base com sobreposicao Grad-CAM quando disponivel.</p>
              </div>
              {selectedFinding && (
                <span className="rounded border border-[#42e8ff]/30 bg-[#42e8ff]/10 px-2 py-1 text-xs font-black text-[#42e8ff]">
                  heatmap ativo
                </span>
              )}
            </div>
          <DicomViewer
            imageUrl={api.imageUrl(id)}
            isDicom={study.image_format === "dicom"}
            heatmapUrl={heatmapUrl}
            showHeatmap={showHeatmap}
            heatmapOpacity={opacity}
          />
          </div>
          <HeatmapOverlayToggle
            enabled={showHeatmap}
            opacity={opacity}
            onToggle={setShowHeatmap}
            onOpacity={setOpacity}
            disabled={!heatmapUrl}
          />
          {!heatmapUrl && prediction && (
            <p className="text-[11px] text-white/45">
              Selecione um achado positivo à esquerda para sobrepor o heatmap.
            </p>
          )}
        </section>

        {/* Human review */}
        <aside className="col-span-12 space-y-4 lg:col-span-3">
          <section className="rx-panel p-4">
          <div>
            <span className="rx-kicker text-[#ffb35c]">Decisao humana</span>
            <h2 className="mt-1 text-lg font-black text-white">Revisão médica</h2>
          </div>
          {review ? (
            <ReviewSummary review={review} prediction={prediction} />
          ) : prediction ? (
            <div className="mt-4">
            <ReviewForm
              findings={prediction.findings}
              predictionId={prediction.prediction_id}
              onSubmit={submitReview}
            />
            </div>
          ) : (
            <p className="mt-4 text-xs leading-5 text-white/45">Rode a análise antes de revisar.</p>
          )}
          </section>

          <section className="rx-panel p-4">
            <span className="rx-kicker">Auditoria</span>
            <h3 className="mt-1 text-base font-black text-white">Trilha do estudo</h3>
            <div className="mt-3">
            <AuditTimeline studyId={id} refreshKey={auditKey} />
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

function ReviewSummary({ review, prediction }: { review: any; prediction: Prediction | null }) {
  const aiByFinding = Object.fromEntries(
    (prediction?.findings || []).map((finding) => [finding.finding_code, finding.is_positive])
  );
  const divergenceCount = review.findings?.filter((finding: any) => finding.diverged_from_ai).length || 0;

  return (
    <div className="mt-4 space-y-3">
      <div className="rounded border border-[#6fa38f]/35 bg-[#6fa38f]/15 p-3 text-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="font-black text-[#8bc2ab]">Decisão: {review.decision}</p>
          <span className={`rounded border px-2 py-1 text-[0.68rem] font-black uppercase tracking-[0.1em] ${
            divergenceCount
              ? "border-[#ffb35c]/35 bg-[#ffb35c]/10 text-[#ffb35c]"
              : "border-[#6fa38f]/35 bg-[#6fa38f]/10 text-[#8bc2ab]"
          }`}>
            {divergenceCount} divergência{divergenceCount === 1 ? "" : "s"}
          </span>
        </div>
        {review.clinical_policy_version && (
          <p className="mt-2 text-[0.68rem] font-black uppercase tracking-[0.1em] text-white/42">
            Política clínica: {review.clinical_policy_version}
          </p>
        )}
        <p className="mt-2 leading-6 text-white/72">{review.final_report}</p>
      </div>

      <div className="space-y-2">
        {review.findings?.map((finding: any) => (
          <div key={finding.finding_code} className="rounded border border-white/10 bg-white/[0.025] p-3 text-xs">
            <div className="font-black text-white/78">{finding.finding_code}</div>
            <div className="mt-2 flex flex-wrap gap-2 font-black uppercase tracking-[0.1em]">
              <span className="rounded border border-white/10 bg-white/[0.03] px-2 py-1 text-white/50">
                IA: {aiByFinding[finding.finding_code] ? "presente" : "ausente"}
              </span>
              <span className="rounded border border-[#42e8ff]/30 bg-[#42e8ff]/10 px-2 py-1 text-[#42e8ff]">
                Médico: {finding.final_label ? "presente" : "ausente"}
              </span>
              {finding.diverged_from_ai && (
                <span className="rounded border border-[#ffb35c]/35 bg-[#ffb35c]/10 px-2 py-1 text-[#ffb35c]">
                  divergência
                </span>
              )}
            </div>
            {finding.comment && (
              <p className="mt-2 leading-5 text-white/55">{finding.comment}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
