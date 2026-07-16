"use client";

import { useEffect, useState } from "react";
import { api, Stats } from "../lib/api";

function Card({ value, label, accent }: { value: string | number; label: string; accent?: string }) {
  return (
    <div className="rx-panel px-4 py-3">
      <div className={`text-2xl font-black leading-none ${accent || "text-white"}`}>{value}</div>
      <div className="mt-2 text-[0.7rem] font-extrabold uppercase tracking-[0.12em] text-white/50">{label}</div>
    </div>
  );
}

export default function StatsPanel({ refreshKey }: { refreshKey?: number }) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(false);
    api
      .stats()
      .then(setStats)
      .catch(() => {
        setStats(null);
        setError(true);
      })
      .finally(() => setLoading(false));
  }, [refreshKey]);

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        {[0, 1, 2, 3, 4].map((item) => (
          <div key={item} className="rx-panel px-4 py-3">
            <div className="h-7 w-12 rounded bg-white/10" />
            <div className="mt-3 h-3 w-24 rounded bg-white/10" />
          </div>
        ))}
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="rx-panel border-critical/30 px-4 py-3 text-sm font-semibold text-white/70">
        Indicadores temporariamente indisponiveis.
      </div>
    );
  }

  const pending = stats.by_status?.predicted || 0;
  const finalized = stats.by_status?.finalized || 0;
  const critical = stats.by_overall_status?.abnormal_critical || 0;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
      <Card value={stats.total_studies} label="Estudos" />
      <Card value={pending} label="Aguardando revisão" accent="text-[#ffb35c]" />
      <Card value={critical} label="Críticos" accent="text-critical" />
      <Card value={finalized} label="Finalizados" accent="text-[#6fa38f]" />
      <Card
        value={`${Math.round(stats.divergence_rate * 100)}%`}
        label="Divergência IA × médico"
      />
    </div>
  );
}
