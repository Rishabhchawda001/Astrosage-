import Link from "next/link";

export default function NotFound() {
  return (
    <main className="relative min-h-screen flex items-center justify-center px-6 bg-surface">
      <div className="text-center z-10">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-gold-400/15 to-gold-500/15 flex items-center justify-center mx-auto mb-6">
          <span className="text-3xl">🕉</span>
        </div>
        <h1 className="font-serif text-5xl font-bold text-text-primary mb-3 tracking-tight">404</h1>
        <p className="text-text-secondary text-lg mb-8 max-w-md">
          This page doesn&apos;t exist yet. The knowledge it would hold remains undiscovered.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gold-500 text-white font-semibold hover:bg-gold-400 transition-all"
        >
          Return Home
        </Link>
      </div>
    </main>
  );
}
