import { Navigation } from "@/components/shared/Navigation";
import { CinematicBackground } from "@/components/landing/CinematicBackground";
import { HeroSection } from "@/components/landing/HeroSection";
import { StorySection } from "@/components/landing/StorySection";
import { CTASection } from "@/components/landing/CTASection";

export default function Home() {
  return (
    <main className="relative min-h-screen">
      <CinematicBackground />
      <Navigation />
      <HeroSection />
      <StorySection />
      <CTASection />

      {/* Footer */}
      <footer className="relative z-10 border-t border-border py-8 px-6 bg-surface/80 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="h-6 w-6 rounded-md bg-gradient-to-br from-gold-500 to-gold-600 flex items-center justify-center">
              <span className="text-white text-[10px] font-bold">🕉</span>
            </div>
            <div>
              <span className="font-serif text-sm text-text-primary tracking-tight">
                AstroSage AI
              </span>
              <p className="text-[10px] text-text-tertiary">
                Ancient Wisdom, Verified
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-[11px] text-text-tertiary">
            <a
              href="https://github.com/Rishabhchawda001/Astrosage-"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-text-secondary transition-colors duration-200"
            >
              GitHub
            </a>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-success/60" />
              Knowledge Freeze v1.0.0
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-gold-500/60" />
              8/8 Quality Gates
            </span>
          </div>
        </div>
      </footer>
    </main>
  );
}
