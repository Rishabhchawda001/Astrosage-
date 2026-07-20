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
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
              <span className="text-surface text-xs font-bold">🕉</span>
            </div>
            <span className="font-serif text-sm text-text-secondary">
              AstroSage AI — Ancient Wisdom, Verified
            </span>
          </div>
          <div className="flex items-center gap-6 text-sm text-text-tertiary">
            <a href="https://github.com/Rishabhchawda001/Astrosage-" className="hover:text-text-secondary transition-colors">
              GitHub
            </a>
            <span>Knowledge Freeze v1.0.0</span>
            <span>8/8 Quality Gates</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
