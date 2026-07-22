"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("AstroSage error:", error);
  }, [error]);

  return (
    <main className="relative min-h-screen flex items-center justify-center px-6 bg-surface">
      <div className="text-center z-10">
        <div className="w-16 h-16 rounded-2xl bg-red-50 flex items-center justify-center mx-auto mb-6">
          <span className="text-3xl">⚠️</span>
        </div>
        <h1 className="font-serif text-4xl font-bold text-text-primary mb-3 tracking-tight">
          Something went wrong
        </h1>
        <p className="text-text-secondary text-lg mb-8 max-w-md">
          An unexpected error occurred while accessing the knowledge base.
          Please try again.
        </p>
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gold-500 text-white font-semibold hover:bg-gold-400 transition-all"
        >
          Try Again
        </button>
      </div>
    </main>
  );
}
