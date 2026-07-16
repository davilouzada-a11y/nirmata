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
            className={`rounded border p-3 transition ${
              f.is_positive ? "border-[#ffb35c]/45 bg-[#ffb35c]/10" : "border-white/10 bg-white/[0.025]"
            } ${f.heatmap_url ? "cursor-pointer hover:bg-white/[0.045]" : ""} ${active ? "ring-1 ring-[#42e8ff]" : ""}`}
          >
            <div className="flex items-center justify-between text-sm">
              <span className={f.is_positive ? "font-black text-[#ffb35c]" : "font-bold text-white/78"}>
                {LABELS[f.finding_code] || f.finding_code}
              </span>
              <span className="font-black tabular-nums text-white">{pct}%</span>
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-black/35">
              <div
                className={`h-full ${f.is_positive ? "bg-[#ffb35c]" : "bg-[#86a8df]/55"}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <div className="mt-2 flex justify-between text-[11px] font-bold text-white/42">
              <span>limiar {Math.round(f.threshold * 100)}%</span>
              {f.heatmap_url && <span>{active ? "ocultar heatmap" : "ver heatmap"}</span>}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
