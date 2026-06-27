import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Radiografia AI — Apoio à decisão",
  description: "Análise de radiografia de tórax com revisão médica obrigatória.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-slate-800 px-6 py-3 flex items-center justify-between">
            <a href="/" className="font-semibold tracking-tight">
              🫁 Radiografia AI
              <span className="ml-2 text-xs text-slate-400 font-normal">
                apoio à decisão · revisão médica obrigatória
              </span>
            </a>
            <span className="text-xs text-warn">
              Resultado automatizado — não substitui o laudo médico
            </span>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
