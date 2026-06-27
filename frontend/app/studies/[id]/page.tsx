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
    try { setPrediction(await api.getPrediction(id)); } catch { setPrediction(null); }
    try { setReview(await api.getReview(id)); } catch { setReview(null); }
  }, [id]);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
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
      ? "bg-critical/20 text-critical"
      : prediction?.overall_status === "abnormal_noncritical"
      ? "bg-warn/20 text-warn"
      : "bg-emerald-900/40 text-emerald-300";

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <Link href="/" className="text-xs text-sky-400 hover:underline">← Fila</Link>
          <h1 className="text-lg font-semibold">
            Paciente {study.patient_code} · {study.view} · <span className="text-slate-400">{study.status}</span>
          </h1>
        </div>
        {prediction && (
          <span className={`rounded-full px-3 py-1 text-xs ${overallBadge}`}>
            {prediction.overall_status} · {prediction.model_version}
          </span>
        )}
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* AI findings */}
        <aside className="col-span-12 lg:col-span-3 space-y-3">
          <h2 className="text-sm font-semibold text-slate-300">Achados da IA</h2>
          {prediction ? (
            <FindingList
              findings={prediction.findings}
              selected={selectedFinding}
              onSelect={setSelectedFinding}
            />
          ) : (
            <button onClick={runPrediction} disabled={busy}
              className="w-full rounded-md bg-sky-600 py-2 text-sm hover:bg-sky-500 disabled:opacity-50">
              {busy ? "Processando…" : "Rodar análise da IA"}
            </button>
          )}
          {prediction && (
            <p className="text-[11px] text-slate-500">{prediction.disclaimer}</p>
          )}
        </aside>

        {/* Viewer */}
        <section className="col-span-12 lg:col-span-6 space-y-2">
          <DicomViewer
            imageUrl={api.imageUrl(id)}
            isDicom={study.image_format === "dicom"}
            heatmapUrl={heatmapUrl}
            showHeatmap={showHeatmap}
            heatmapOpacity={opacity}
          />
          <HeatmapOverlayToggle
            enabled={showHeatmap}
            opacity={opacity}
            onToggle={setShowHeatmap}
            onOpacity={setOpacity}
            disabled={!heatmapUrl}
          />
          {!heatmapUrl && prediction && (
            <p className="text-[11px] text-slate-500">
              Selecione um achado positivo à esquerda para sobrepor o heatmap.
            </p>
          )}
        </section>

        {/* Human review */}
        <aside className="col-span-12 lg:col-span-3 space-y-4">
          <h2 className="text-sm font-semibold text-slate-300">Revisão médica</h2>
          {review ? (
            <div className="rounded-lg border border-emerald-700 bg-emerald-900/20 p-3 text-sm">
              <p className="font-medium">Decisão: {review.decision}</p>
              <p className="mt-1 text-slate-300">{review.final_report}</p>
            </div>
          ) : prediction ? (
            <ReviewForm
              findings={prediction.findings}
              predictionId={prediction.prediction_id}
              onSubmit={submitReview}
            />
          ) : (
            <p className="text-xs text-slate-500">Rode a análise antes de revisar.</p>
          )}

          <div>
            <h3 className="mb-1 text-xs font-semibold uppercase text-slate-500">Auditoria</h3>
            <AuditTimeline studyId={id} refreshKey={auditKey} />
          </div>
        </aside>
      </div>
    </div>
  );
}
