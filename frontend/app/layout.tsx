import type { Metadata } from "next";
import "./globals.css";
import { NavLinks } from "@/components/NavLinks";

export const metadata: Metadata = {
  title: "Tea Packaging Optimizer",
  description:
    "AI-assisted packaging, carton, pallet, and container optimization for tea exports.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex bg-ink text-paper">
        <aside className="w-60 shrink-0 border-r border-border bg-surface flex flex-col">
          <div className="px-6 py-6 border-b border-border relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-copper via-teal to-copper" />
            <div className="font-display font-bold text-lg tracking-tight text-paper">
              Innovacio
            </div>
            <div className="text-xs text-muted mt-0.5 tracking-wide uppercase">
              Tea Packaging AI
            </div>
          </div>
          <NavLinks />
          <div className="px-6 py-4 border-t border-border text-xs text-muted">
            Container Optimization
            <br />
            Assessment Build
          </div>
        </aside>
        <main className="flex-1 bg-ink min-h-screen">{children}</main>
      </body>
    </html>
  );
}
