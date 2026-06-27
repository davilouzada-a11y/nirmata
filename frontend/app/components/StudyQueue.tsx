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

  useEffect(() => {
    api.listStudies().then(setStudies).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="text-critical">{error}</p>;
  if (!studies.length) return <p className="text-slate-400">Nenhum estudo na fila.</p>;

  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr className="text-left text-xs uppercase text-slate-400">
          <th className="py-2">Prioridade</th>
          <th>Paciente</th>
          <th>Incidência</th>
          <th>Status</th>
          <th>IA</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {studies.map((s) => (
          <tr key={s.id} className="border-t border-slate-800">
            <td className="py-2">
              {s.priority === "critical" ? (
                <span className="rounded-full bg-critical/20 px-2 py-0.5 text-xs text-critical">⚠ crítico</span>
              ) : (
                <span className="text-xs text-slate-500">rotina</span>
              )}
            </td>
            <td>{s.patient_code}</td>
            <td>{s.view}</td>
            <td>{STATUS_LABEL[s.status] || s.status}</td>
            <td className="text-slate-400">{s.overall_status || "—"}</td>
            <td>
              <Link href={`/studies/${s.id}`} className="text-sky-400 hover:underline">
                Abrir
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
