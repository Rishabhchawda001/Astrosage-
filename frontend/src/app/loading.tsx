export default function Loading() {
  return (
    <main className="relative min-h-screen flex items-center justify-center">
      <div className="flex flex-col items-center gap-4 z-10">
        <div className="w-12 h-12 rounded-full border-2 border-gold-500/20 border-t-gold-500 animate-spin" />
        <p className="text-text-tertiary text-sm">Loading knowledge...</p>
      </div>
    </main>
  );
}
