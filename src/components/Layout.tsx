import type { ReactNode } from "react";
import Navbar from "./Navbar";

interface Props {
  children: ReactNode;
  /** Wider max-width for voice/video call layouts. */
  wide?: boolean;
}

export default function Layout({ children, wide = false }: Props) {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className={`mx-auto w-full flex-1 px-4 py-8 ${wide ? "max-w-7xl" : "max-w-6xl"}`}>
        {children}
      </main>
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        Practice environment for counseling education. AI feedback supports learning and is not a
        clinical evaluation.
      </footer>
    </div>
  );
}
