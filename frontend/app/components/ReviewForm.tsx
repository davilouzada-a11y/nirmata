"use client";

import { useState } from "react";
import { Finding } from "../lib/api";

const LABELS: Record<string, string> = {
  normal_no_critical_finding: "Sem achado crítico",
  pneumothorax: "Pneumotórax",
  pleural_effusion: "Derrame pleural",
  consolidation: "Consolidação",
  lung_opacity: "Opacidade pulmonar",
  cardiomegaly: "Cardiomegalia",
};

interface Props {
  findings: Finding[];
  predictionId: string;
  onSubmit: (payload: {
    decision: string;
    prediction_id: string;
    final_findings: { finding_code: string; final_label: boolean; comment?: string }[];
    final_report: string;
  }) => Promise<void>;
}

export default function ReviewForm({ findings, predictionId, onSubmit }: Props) {
  // Seed the human labels from the AI suggestion; the radiologist edits them.
  const [labels, setLabels] = useState<Record<string, boolean>>(
    Object.fromEntries(findings.map((f) => [f.finding_code, f.is_positive]))
  );
  const [comments, setComments] = useState<Record<string, string>>({});
  const [report, setReport] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const diverged = findings.some((f) => labels[f.finding_code] !== f.is_positive);
  const divergenceCount = findings.filter((f) => labels[f.finding_code] !== f.is_positive).length;

  async function submit(decision: string) {
    if (!report.trim()) {
      alert("O laudo final é obrigatório.");
      return;
    }
    setSubmitting(true);
    try {
      await onSubmit({
        decision,
        prediction_id: predictionId,
        final_report: report,
        final_findings: findings.map((f) => ({
          finding_code: f.finding_code,
          final_label: labels[f.finding_code],
          comment: comments[f.finding_code]?.trim()
            || (labels[f.finding_code] !== f.is_positive ? "Ajustado pelo revisor" : undefined),
        })),
      });
      setDone(true);
    } catch (err) {
      alert((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return <p className="rounded border border-[#6fa38f]/35 bg-[#6fa38f]/15 p-3 text-sm text-[#8bc2ab]">
      Revisão registrada. Estudo finalizado.
    </p>;
  }

  return (
    <div className="space-y-4">
      <div className="rounded border border-[#ffb35c]/25 bg-[#ffb35c]/10 p-3">
        <p className="text-xs font-bold leading-5 text-white/72">
          Confirme ou ajuste cada achado. A decisão humana é obrigatória,
          versionada contra esta inferência e fica registrada na auditoria.
        </p>
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div className="rounded border border-white/10 bg-white/[0.03] p-2">
            <span className="block font-black text-white">{findings.length}</span>
            <span className="rx-kicker text-white/45">achados IA</span>
          </div>
          <div className="rounded border border-white/10 bg-white/[0.03] p-2">
            <span className={`block font-black ${divergenceCount ? "text-[#ffb35c]" : "text-[#8bc2ab]"}`}>
              {divergenceCount}
            </span>
            <span className="rx-kicker text-white/45">divergências</span>
          </div>
        </div>
      </div>

      <ul className="space-y-2">
        {findings.map((f) => (
          <li key={f.finding_code} className="rounded border border-white/10 bg-white/[0.025] p-3 text-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="font-black text-white/82">{LABELS[f.finding_code] || f.finding_code}</span>
                <div className="mt-2 flex flex-wrap gap-2 text-[0.68rem] font-black uppercase tracking-[0.1em]">
                  <span className={`rounded border px-2 py-1 ${
                    f.is_positive
                      ? "border-[#ffb35c]/35 bg-[#ffb35c]/10 text-[#ffb35c]"
                      : "border-[#6fa38f]/35 bg-[#6fa38f]/10 text-[#8bc2ab]"
                  }`}>
                    IA: {f.is_positive ? "presente" : "ausente"}
                  </span>
                  <span className={`rounded border px-2 py-1 ${
                    labels[f.finding_code]
                      ? "border-[#42e8ff]/35 bg-[#42e8ff]/10 text-[#42e8ff]"
                      : "border-white/10 bg-white/[0.03] text-white/50"
                  }`}>
                    Médico: {labels[f.finding_code] ? "presente" : "ausente"}
                  </span>
                  {labels[f.finding_code] !== f.is_positive && (
                    <span className="rounded border border-[#ffb35c]/35 bg-[#ffb35c]/10 px-2 py-1 text-[#ffb35c]">
                      divergência
                    </span>
                  )}
                </div>
              </div>
              <label className="flex shrink-0 items-center gap-2 text-xs font-bold text-white/60">
                <input
                  type="checkbox"
                  checked={labels[f.finding_code]}
                  onChange={(e) => setLabels({ ...labels, [f.finding_code]: e.target.checked })}
                />
                presente
              </label>
            </div>
            <label className="mt-3 block text-[0.68rem] font-extrabold uppercase tracking-[0.12em] text-white/42">
              Comentário do revisor
              <input
                value={comments[f.finding_code] || ""}
                onChange={(e) => setComments({ ...comments, [f.finding_code]: e.target.value })}
                placeholder="Opcional"
                className="rx-field mt-1 w-full px-3 py-2 text-sm normal-case tracking-normal"
              />
            </label>
          </li>
        ))}
      </ul>

      <label className="block">
        <span className="rx-label">Laudo final</span>
      <textarea
        value={report}
        onChange={(e) => setReport(e.target.value)}
        placeholder="Laudo final (obrigatório)"
        className="rx-field h-28 w-full p-3 text-sm"
      />
      </label>

      <div className="flex flex-wrap gap-2">
        <button disabled={submitting} onClick={() => submit("confirmed")}
          className="rounded bg-[#6fa38f] px-3 py-2 text-sm font-black text-[#06110d] hover:bg-[#8bc2ab] disabled:opacity-50">
          Confirmar
        </button>
        <button disabled={submitting} onClick={() => submit("corrected")}
          className="rounded bg-[#ffb35c] px-3 py-2 text-sm font-black text-[#1b1005] hover:bg-[#ffc77f] disabled:opacity-50">
          Corrigir{diverged ? " (alterado)" : ""}
        </button>
        <button disabled={submitting} onClick={() => submit("rejected")}
          className="rounded bg-critical px-3 py-2 text-sm font-black text-white hover:brightness-110 disabled:opacity-50">
          Rejeitar IA
        </button>
      </div>
    </div>
  );
}
