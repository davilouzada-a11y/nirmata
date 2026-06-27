"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, getToken, clearToken } from "./lib/api";
import StudyQueue from "./components/StudyQueue";
import StatsPanel from "./components/StatsPanel";

export default function HomePage() {
  const router = useRouter();
  const [authChecked, setAuthChecked] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api.me().then(() => setAuthChecked(true)).catch(() => router.replace("/login"));
  }, [router]);

  async function onUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      await api.upload(form);
      (e.target as HTMLFormElement).reset();
      setRefreshKey((k) => k + 1);
    } catch (err) {
      alert((err as Error).message);
    }
  }

  if (!authChecked) return <p className="p-6 text-slate-400">Carregando…</p>;

  return (
    <div className="mx-auto max-w-5xl p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Fila de estudos</h1>
        <div className="flex items-center gap-4 text-xs">
          <Link href="/models" className="text-slate-400 hover:text-slate-200">Modelos</Link>
          <button
            onClick={() => { clearToken(); router.replace("/login"); }}
            className="text-slate-400 hover:text-slate-200"
          >
            Sair
          </button>
        </div>
      </div>

      <StatsPanel refreshKey={refreshKey} />

      <form onSubmit={onUpload} className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-800 bg-slate-900 p-4">
        <div>
          <label className="block text-xs text-slate-400">Código do paciente</label>
          <input name="patient_code" required placeholder="P-001"
            className="mt-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-slate-400">Incidência</label>
          <select name="view" className="mt-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm">
            <option>PA</option><option>AP</option><option>LAT</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400">Imagem (DICOM/PNG/JPG)</label>
          <input name="file" type="file" required accept=".dcm,.dicom,image/*"
            className="mt-1 text-sm" />
        </div>
        <button className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium hover:bg-sky-500">
          Enviar estudo
        </button>
      </form>

      <StudyQueue key={refreshKey} />
    </div>
  );
}
