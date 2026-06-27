"use client";

import { useState } from "react";
import { Finding } from "../lib/api";

const LABELS: Record<string, string> = {
  normal_no_critical_finding: "Sem achado crítico",
  pneumothorax: "Pneumotórax",
  pleural_effusion: "Derrame pleural",
  consolidation: "Consolidação / opacidade",
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
  const [report, setReport] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const diverged = findings.some((f) => labels[f.finding_code] !== f.is_positive);

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
          comment: labels[f.finding_code] !== f.is_positive ? "Ajustado pelo revisor" : undefined,
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
    return <p className="rounded-lg border border-emerald-700 bg-emerald-900/30 p-3 text-sm">
      Revisão registrada. Estudo finalizado.
    </p>;
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-400">
        Confirme ou ajuste cada achado. A decisão humana é obrigatória e fica registrada.
      </p>
      <ul className="space-y-1">
        {findings.map((f) => (
          <li key={f.finding_code} className="flex items-center justify-between text-sm">
            <span>{LABELS[f.finding_code] || f.finding_code}</span>
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={labels[f.finding_code]}
                onChange={(e) => setLabels({ ...labels, [f.finding_code]: e.target.checked })}
              />
              presente
              {labels[f.finding_code] !== f.is_positive && (
                <span className="text-warn">≠ IA</span>
              )}
            </label>
          </li>
        ))}
      </ul>

      <textarea
        value={report}
        onChange={(e) => setReport(e.target.value)}
        placeholder="Laudo final (obrigatório)"
        className="h-24 w-full rounded-md border border-slate-700 bg-slate-950 p-2 text-sm"
      />

      <div className="flex flex-wrap gap-2">
        <button disabled={submitting} onClick={() => submit("confirmed")}
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm hover:bg-emerald-500 disabled:opacity-50">
          Confirmar
        </button>
        <button disabled={submitting} onClick={() => submit("corrected")}
          className="rounded-md bg-amber-600 px-3 py-2 text-sm hover:bg-amber-500 disabled:opacity-50">
          Corrigir{diverged ? " (alterado)" : ""}
        </button>
        <button disabled={submitting} onClick={() => submit("rejected")}
          className="rounded-md bg-rose-600 px-3 py-2 text-sm hover:bg-rose-500 disabled:opacity-50">
          Rejeitar IA
        </button>
      </div>
    </div>
  );
}
