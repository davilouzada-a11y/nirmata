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
      router.replace("/login?next=/");
      return;
    }
    api.me().then(() => setAuthChecked(true)).catch(() => router.replace("/login?next=/"));
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
    <div className="mx-auto max-w-7xl px-5 py-8 md:py-12">
      <section className="mb-6 grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div>
          <span className="rx-kicker">Leitura assistida de radiografia de torax</span>
          <h1 className="mt-3 max-w-4xl text-4xl font-black leading-[0.98] tracking-normal text-white md:text-6xl">
            Worklist radiografica com triagem e revisao humana
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-7 text-[#b9d7e8] md:text-lg">
            DOD Rx organiza estudos de torax, achados sugeridos pela IA, prioridade
            clinica e auditoria. A IA apoia a leitura; a decisao final permanece humana.
          </p>
        </div>

        <aside className="rx-panel-strong p-5">
          <div className="rx-kicker text-[#ffb35c]">Governanca clinica</div>
          <dl className="mt-5 grid gap-4 text-sm">
            <div className="border-t border-white/15 pt-4">
              <dt className="font-black text-white">Escopo inicial</dt>
              <dd className="mt-1 text-white/65">Radiografia de torax - PA, AP ou LAT.</dd>
            </div>
            <div className="border-t border-white/15 pt-4">
              <dt className="font-black text-white">Saida IA</dt>
              <dd className="mt-1 text-white/65">Triagem, achados sugeridos e heatmaps.</dd>
            </div>
            <div className="border-t border-white/15 pt-4">
              <dt className="font-black text-white">Finalizacao</dt>
              <dd className="mt-1 text-white/65">Bloqueada sem revisao humana registrada.</dd>
            </div>
          </dl>
        </aside>
      </section>

      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <span className="rx-kicker">Bancada RX</span>
          <h2 className="mt-1 text-xl font-black text-white">Fila de estudos</h2>
        </div>
        <div className="flex items-center gap-3 text-xs font-bold">
          <Link href="/models" className="rounded border border-white/10 px-3 py-2 text-white/65 hover:bg-[#86a8df]/10 hover:text-white">Modelos</Link>
          <Link href="/governance" className="rounded border border-white/10 px-3 py-2 text-white/65 hover:bg-[#86a8df]/10 hover:text-white">Governança</Link>
          <button
            onClick={() => { clearToken(); router.replace("/login"); }}
            className="rounded border border-white/10 px-3 py-2 text-white/65 hover:bg-white/5 hover:text-white"
          >
            Sair
          </button>
        </div>
      </div>

      <StatsPanel refreshKey={refreshKey} />

      <form onSubmit={onUpload} className="rx-panel my-6 grid gap-4 p-4 md:grid-cols-[minmax(160px,1fr)_150px_minmax(260px,1.4fr)_auto] md:items-end">
        <div>
          <label htmlFor="upload-patient-code" className="rx-label block">Código do paciente</label>
          <input id="upload-patient-code" name="patient_code" required placeholder="P-001"
            autoComplete="off"
            className="rx-field mt-1 w-full px-3 py-2 text-sm" />
        </div>
        <div>
          <label htmlFor="upload-view" className="rx-label block">Incidência</label>
          <select id="upload-view" name="view" className="rx-field mt-1 w-full px-3 py-2 text-sm">
            <option>PA</option><option>AP</option><option>LAT</option>
          </select>
        </div>
        <div>
          <label htmlFor="upload-file" className="rx-label block">Imagem (DICOM/PNG/JPG)</label>
          <input id="upload-file" name="file" type="file" required accept=".dcm,.dicom,image/*"
            aria-describedby="upload-file-help"
            className="mt-1 w-full text-sm text-[#b9d7e8] file:mr-3 file:rounded file:border file:border-white/15 file:bg-white/5 file:px-3 file:py-2 file:text-sm file:font-bold file:text-white hover:file:bg-white/10" />
          <p id="upload-file-help" className="sr-only">
            Aceita arquivos DICOM, PNG ou JPG de radiografia.
          </p>
        </div>
        <button className="min-h-[42px] rounded bg-white px-5 py-2 text-sm font-black text-[#07090d] transition hover:-translate-y-0.5 hover:bg-white/90">
          Enviar estudo
        </button>
      </form>

      <StudyQueue key={refreshKey} />
    </div>
  );
}
