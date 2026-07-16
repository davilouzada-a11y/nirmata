"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { login } from "../lib/api";

export default function LoginPage() {
  return (
    <Suspense fallback={<p className="p-6 text-slate-400">Carregando…</p>}>
      <LoginContent />
    </Suspense>
  );
}

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/";
  const [email, setEmail] = useState("radiologista@example.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push(next.startsWith("/") ? next : "/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto grid min-h-[calc(100vh-76px)] max-w-7xl items-center gap-8 px-5 py-10 lg:grid-cols-[minmax(0,1fr)_390px]">
      <section>
        <span className="rx-kicker">Acesso DOD Rx</span>
        <h1 className="mt-3 max-w-4xl text-4xl font-black leading-[0.98] text-white md:text-6xl">
          Bancada radiografica com revisao humana obrigatoria
        </h1>
        <p className="mt-5 max-w-2xl text-base leading-7 text-[#b9d7e8] md:text-lg">
          Entre para acessar worklist, viewer, achados sugeridos pela IA, trilha de
          auditoria e governanca de modelos. O fluxo mantem a decisao clinica final
          com o revisor humano.
        </p>
        <div className="mt-8 grid max-w-2xl gap-3 sm:grid-cols-3">
          <div className="rx-panel p-4">
            <div className="text-2xl font-black text-white">RX</div>
            <div className="mt-2 text-[0.7rem] font-extrabold uppercase tracking-[0.12em] text-white/50">torax MVP</div>
          </div>
          <div className="rx-panel p-4">
            <div className="text-2xl font-black text-[#ffb35c]">IA</div>
            <div className="mt-2 text-[0.7rem] font-extrabold uppercase tracking-[0.12em] text-white/50">advisory</div>
          </div>
          <div className="rx-panel p-4">
            <div className="text-2xl font-black text-[#6fa38f]">HITL</div>
            <div className="mt-2 text-[0.7rem] font-extrabold uppercase tracking-[0.12em] text-white/50">revisao</div>
          </div>
        </div>
      </section>

      <form onSubmit={onSubmit} className="rx-panel-strong space-y-5 p-6">
        <div>
          <span className="rx-kicker text-[#ffb35c]">Credenciais</span>
          <h2 className="mt-2 text-2xl font-black text-white">Entrar</h2>
        </div>
        <div>
          <label htmlFor="login-email" className="rx-label">E-mail</label>
          <input
            id="login-email"
            className="rx-field mt-1 w-full px-3 py-2 text-sm"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            autoComplete="email"
          />
        </div>
        <div>
          <label htmlFor="login-password" className="rx-label">Senha</label>
          <input
            id="login-password"
            className="rx-field mt-1 w-full px-3 py-2 text-sm"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            autoComplete="current-password"
          />
        </div>
        {error && <p className="rounded border border-critical/35 bg-critical/10 p-3 text-sm font-bold text-critical">{error}</p>}
        <button
          disabled={loading}
          className="w-full rounded bg-white py-3 text-sm font-black text-[#07090d] transition hover:-translate-y-0.5 hover:bg-white/90 disabled:opacity-50"
        >
          {loading ? "Entrando…" : "Entrar"}
        </button>
        <p className="border-t border-white/10 pt-4 text-xs leading-5 text-white/45">
          Resultado automatizado nao substitui laudo medico. Todo aceite clinico
          requer revisao humana registrada.
        </p>
      </form>
    </div>
  );
}
