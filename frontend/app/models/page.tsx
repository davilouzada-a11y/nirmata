"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, getToken, ModelVersion } from "../lib/api";

export default function ModelsPage() {
  const router = useRouter();
  const [versions, setVersions] = useState<ModelVersion[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    api.modelVersions().then(setVersions).catch((e) => setError(e.message));
  }, [router]);

  return (
    <div className="mx-auto max-w-4xl p-6 space-y-4">
      <Link href="/" className="text-xs text-sky-400 hover:underline">← Fila</Link>
      <h1 className="text-xl font-semibold">Registro de modelos</h1>
      <p className="text-xs text-slate-400">
        Cada predição referencia a versão exata do modelo usada, garantindo rastreabilidade.
      </p>

      {error && <p className="text-critical">{error}</p>}

      <div className="space-y-3">
        {versions.map((m) => (
          <div key={m.id} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <div className="flex items-center justify-between">
              <span className="font-medium">{m.version}</span>
              <span className="text-xs text-slate-500">
                {new Date(m.created_at).toLocaleDateString()}
              </span>
            </div>
            <p className="text-sm text-slate-300">{m.name}</p>
            {m.training_dataset && (
              <p className="text-xs text-slate-500">Dataset: {m.training_dataset}</p>
            )}
            <div className="mt-2 flex flex-wrap gap-2">
              {Object.entries(m.threshold_config || {}).map(([code, thr]) => (
                <span key={code} className="rounded-full border border-slate-700 px-2 py-0.5 text-[11px] text-slate-400">
                  {code}: {Math.round(Number(thr) * 100)}%
                </span>
              ))}
            </div>
          </div>
        ))}
        {!versions.length && !error && <p className="text-slate-400">Nenhum modelo registrado.</p>}
      </div>
    </div>
  );
}
