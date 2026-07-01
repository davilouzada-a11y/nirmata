"use client";

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
  selected: string | null;
  onSelect: (code: string | null) => void;
}

export default function FindingList({ findings, selected, onSelect }: Props) {
  return (
    <ul className="space-y-2">
      {findings.map((f) => {
        const pct = Math.round(f.probability * 100);
        const active = selected === f.finding_code;
        return (
          <li
            key={f.finding_code}
            onClick={() => f.heatmap_url && onSelect(active ? null : f.finding_code)}
            className={`rounded-lg border p-2 ${
              f.is_positive ? "border-warn/60 bg-warn/5" : "border-slate-800"
            } ${f.heatmap_url ? "cursor-pointer" : ""} ${active ? "ring-1 ring-sky-500" : ""}`}
          >
            <div className="flex items-center justify-between text-sm">
              <span className={f.is_positive ? "font-medium text-warn" : ""}>
                {LABELS[f.finding_code] || f.finding_code}
              </span>
              <span className="tabular-nums">{pct}%</span>
            </div>
            <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
              <div
                className={`h-full ${f.is_positive ? "bg-warn" : "bg-slate-600"}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <div className="mt-1 flex justify-between text-[11px] text-slate-500">
              <span>limiar {Math.round(f.threshold * 100)}%</span>
              {f.heatmap_url && <span>{active ? "ocultar heatmap" : "ver heatmap"}</span>}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
