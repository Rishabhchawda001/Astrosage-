export default function Loading() {
  return (
    <main className="relative min-h-screen flex items-center justify-center bg-surface">
      <div className="flex flex-col items-center gap-4 z-10">
        <div className="w-10 h-10 rounded-full border-2 border-gold-500/15 border-t-gold-500 animate-spin" />
        <p className="text-text-tertiary text-sm">Loading knowledge...</p>
      </div>
    </main>
  );
}
