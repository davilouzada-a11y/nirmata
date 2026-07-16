"use client";

import { useEffect, useState } from "react";
import { api } from "../lib/api";

interface AuditEntry {
  action: string;
  user_id: string | null;
  payload: Record<string, unknown> | null;
  created_at: string;
}

const ACTION_LABEL: Record<string, string> = {
  "study.upload": "Estudo enviado",
  "study.predict": "Inferência executada",
  "study.review": "Revisão médica registrada",
};

export default function AuditTimeline({ studyId, refreshKey }: { studyId: string; refreshKey: number }) {
  const [entries, setEntries] = useState<AuditEntry[]>([]);

  useEffect(() => {
    api.auditTrail(studyId).then(setEntries).catch(() => setEntries([]));
  }, [studyId, refreshKey]);

  if (!entries.length) return <p className="text-xs text-white/45">Sem eventos.</p>;

  return (
    <ol className="space-y-3 text-xs">
      {entries.map((e, i) => (
        <li key={i} className="border-l border-[#42e8ff]/35 pl-3">
          <span className="block font-bold text-white/38">{new Date(e.created_at).toLocaleString()}</span>
          <span className="mt-1 block font-black text-white/78">{ACTION_LABEL[e.action] || e.action}</span>
        </li>
      ))}
    </ol>
  );
}
