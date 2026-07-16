import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DOD Rx - Apoio a decisao radiografica",
  description: "Leitura assistida de radiografia de torax com revisao humana obrigatoria.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <div className="min-h-screen">
          <header className="sticky top-0 z-20 border-b border-white/10 bg-[#06070b]/85 px-5 backdrop-blur-2xl">
            <div className="mx-auto flex min-h-[76px] max-w-7xl items-center justify-between gap-5">
              <a href="/" className="inline-flex min-w-0 items-center gap-3 text-white">
                <span className="grid h-[38px] w-[38px] place-items-center rounded border border-white/20 text-sm font-black text-[#42e8ff]">
                  D
                </span>
                <span className="grid leading-none">
                  <strong className="text-sm font-black tracking-[0.08em]">DOD RX</strong>
                  <small className="mt-1 text-[0.58rem] font-semibold tracking-[0.18em] text-white/60">
                    PERFORMANCE
                  </small>
                </span>
            </a>
              <div className="hidden items-center gap-3 text-xs font-bold text-white/60 md:flex">
                <a className="rounded px-3 py-2 hover:bg-[#86a8df]/10 hover:text-white" href="/">
                  Fila RX
                </a>
                <a className="rounded px-3 py-2 hover:bg-[#86a8df]/10 hover:text-white" href="/models">
                  Modelos
                </a>
                <a className="rounded px-3 py-2 hover:bg-[#86a8df]/10 hover:text-white" href="/governance">
                  Governança
                </a>
                <span className="rounded border border-white/10 px-3 py-2 text-[#ffb35c]">
                  IA advisory - revisao obrigatoria
                </span>
              </div>
            </div>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
