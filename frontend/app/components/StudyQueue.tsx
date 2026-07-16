"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, StudyListItem } from "../lib/api";

const STATUS_LABEL: Record<string, string> = {
  uploaded: "Enviado",
  processing: "Processando",
  predicted: "Predito",
  under_review: "Em revisão",
  reviewed: "Revisado",
  finalized: "Finalizado",
};

export default function StudyQueue() {
  const [studies, setStudies] = useState<StudyListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .listStudies()
      .then(setStudies)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rx-panel overflow-hidden">
        <QueueHeader />
        <div className="space-y-3 p-4 md:hidden">
          {[0, 1, 2].map((item) => (
            <div key={item} className="rounded border border-white/10 bg-white/[0.025] p-4">
              <div className="h-3 w-20 rounded bg-white/10" />
              <div className="mt-4 h-5 w-36 rounded bg-white/10" />
              <div className="mt-3 grid grid-cols-2 gap-3">
                <div className="h-3 rounded bg-white/10" />
                <div className="h-3 rounded bg-white/10" />
              </div>
            </div>
          ))}
        </div>
        <div className="hidden p-4 md:block">
          <div className="space-y-3">
            {[0, 1, 2, 3].map((item) => (
              <div key={item} className="grid grid-cols-6 gap-4">
                <div className="h-4 rounded bg-white/10" />
                <div className="h-4 rounded bg-white/10" />
                <div className="h-4 rounded bg-white/10" />
                <div className="h-4 rounded bg-white/10" />
                <div className="h-4 rounded bg-white/10" />
                <div className="h-4 rounded bg-white/10" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rx-panel border-critical/30 p-5">
        <span className="rx-kicker text-critical">Worklist indisponivel</span>
        <p className="mt-2 text-sm font-semibold text-white/80">{error}</p>
      </div>
    );
  }

  if (!studies.length) {
    return (
      <div className="rx-panel p-5">
        <span className="rx-kicker">Worklist</span>
        <h2 className="mt-3 text-xl font-black text-white">Nenhum estudo na fila.</h2>
        <p className="mt-2 max-w-xl text-sm leading-6 text-[#b9d7e8]">
          Envie uma radiografia para iniciar triagem, achados sugeridos pela IA
          e revisao humana obrigatoria.
        </p>
      </div>
    );
  }

  return (
    <div className="rx-panel overflow-hidden">
      <QueueHeader />
      <div className="grid gap-3 p-4 md:hidden">
        {studies.map((s) => (
          <article key={s.id} className="rounded border border-white/10 bg-white/[0.025] p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <PriorityBadge priority={s.priority} />
                <h3 className="mt-3 text-lg font-black leading-tight text-white">{s.patient_code}</h3>
              </div>
              <Link
                href={`/studies/${s.id}`}
                className="shrink-0 rounded border border-white/10 px-3 py-2 text-xs font-black text-[#42e8ff] hover:bg-[#42e8ff]/10"
              >
                Abrir
              </Link>
            </div>
            <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-[0.66rem] font-extrabold uppercase tracking-[0.12em] text-white/40">Incidencia</dt>
                <dd className="mt-1 font-semibold text-white/82">{s.view}</dd>
              </div>
              <div>
                <dt className="text-[0.66rem] font-extrabold uppercase tracking-[0.12em] text-white/40">Status</dt>
                <dd className="mt-1 font-semibold text-white/82">{STATUS_LABEL[s.status] || s.status}</dd>
              </div>
              <div className="col-span-2">
                <dt className="text-[0.66rem] font-extrabold uppercase tracking-[0.12em] text-white/40">IA</dt>
                <dd className="mt-1 font-semibold text-[#b9d7e8]">{s.overall_status || "-"}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <thead>
            <tr className="text-left text-[0.68rem] uppercase tracking-[0.14em] text-white/45">
              <th className="px-4 py-3">Prioridade</th>
              <th className="px-4 py-3">Paciente</th>
              <th className="px-4 py-3">Incidência</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">IA</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {studies.map((s) => (
              <tr key={s.id} className="border-t border-white/10 text-white/82 hover:bg-white/[0.035]">
                <td className="px-4 py-3">
                  <PriorityBadge priority={s.priority} />
                </td>
                <td className="px-4 py-3 font-bold text-white">{s.patient_code}</td>
                <td className="px-4 py-3">{s.view}</td>
                <td className="px-4 py-3">{STATUS_LABEL[s.status] || s.status}</td>
                <td className="px-4 py-3 text-[#b9d7e8]">{s.overall_status || "-"}</td>
                <td className="px-4 py-3 text-right">
                  <Link href={`/studies/${s.id}`} className="rounded border border-white/10 px-3 py-2 text-xs font-black text-[#42e8ff] hover:bg-[#42e8ff]/10">
                    Abrir
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function QueueHeader() {
  return (
    <div className="border-b border-white/10 px-4 py-3">
      <span className="rx-kicker">Worklist</span>
    </div>
  );
}

function PriorityBadge({ priority }: { priority: string }) {
  if (priority === "critical") {
    return (
      <span className="rounded border border-critical/30 bg-critical/15 px-2 py-1 text-xs font-black text-critical">
        critico
      </span>
    );
  }

  return <span className="text-xs font-bold text-white/42">rotina</span>;
}
