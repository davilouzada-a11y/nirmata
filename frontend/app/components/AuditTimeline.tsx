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

  if (!entries.length) return <p className="text-xs text-slate-500">Sem eventos.</p>;

  return (
    <ol className="space-y-2 text-xs">
      {entries.map((e, i) => (
        <li key={i} className="flex gap-2">
          <span className="text-slate-600">{new Date(e.created_at).toLocaleString()}</span>
          <span>{ACTION_LABEL[e.action] || e.action}</span>
        </li>
      ))}
    </ol>
  );
}
