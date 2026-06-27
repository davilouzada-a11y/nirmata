"use client";

import { useEffect, useState } from "react";
import { api, Stats } from "../lib/api";

function Card({ value, label, accent }: { value: string | number; label: string; accent?: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-3">
      <div className={`text-2xl font-semibold ${accent || ""}`}>{value}</div>
      <div className="text-xs text-slate-400">{label}</div>
    </div>
  );
}

export default function StatsPanel({ refreshKey }: { refreshKey?: number }) {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    api.stats().then(setStats).catch(() => setStats(null));
  }, [refreshKey]);

  if (!stats) return null;

  const pending = stats.by_status?.predicted || 0;
  const finalized = stats.by_status?.finalized || 0;
  const critical = stats.by_overall_status?.abnormal_critical || 0;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
      <Card value={stats.total_studies} label="Estudos" />
      <Card value={pending} label="Aguardando revisão" accent="text-warn" />
      <Card value={critical} label="Críticos" accent="text-critical" />
      <Card value={finalized} label="Finalizados" accent="text-emerald-400" />
      <Card
        value={`${Math.round(stats.divergence_rate * 100)}%`}
        label="Divergência IA × médico"
      />
    </div>
  );
}
