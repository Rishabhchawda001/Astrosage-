import { Navigation } from "@/components/shared/Navigation";
import { StarField } from "@/components/landing/StarField";
import { HeroSection } from "@/components/landing/HeroSection";
import { StorySection } from "@/components/landing/StorySection";
import { CTASection } from "@/components/landing/CTASection";

export default function Home() {
  return (
    <main className="relative min-h-screen">
      <StarField />
      <Navigation />
      <HeroSection />
      <StorySection />
      <CTASection />

      {/* Footer */}
      <footer className="relative z-10 border-t border-border py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
              <span className="text-surface text-xs font-bold">🕉</span>
            </div>
            <div>
              <span className="font-serif text-sm text-text-secondary">
                AstroSage AI
              </span>
              <p className="text-[11px] text-text-tertiary">
                Ancient Wisdom, Verified
              </p>
            </div>
          </div>
          <div className="flex items-center gap-6 text-xs text-text-tertiary">
            <a
              href="https://github.com/Rishabhchawda001/Astrosage-"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-text-secondary transition-colors"
            >
              GitHub
            </a>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400/60" />
              Knowledge Freeze v1.0.0
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-gold-400/60" />
              8/8 Quality Gates
            </span>
          </div>
        </div>
      </footer>
    </main>
  );
}
