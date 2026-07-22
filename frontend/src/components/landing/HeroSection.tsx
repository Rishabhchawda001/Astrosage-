"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, ShieldCheck } from "lucide-react";

function StatItem({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <div className="text-2xl sm:text-3xl font-bold gradient-gold font-serif tracking-tight">
        {value}
      </div>
      <div className="text-[11px] sm:text-xs text-text-tertiary mt-1.5 tracking-wide">
        {label}
      </div>
    </div>
  );
}

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      <div className="relative z-10 max-w-4xl mx-auto px-6 text-center pt-28 pb-20">
        {/* Trust badge */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/50 backdrop-blur-md text-[13px] text-gold-700 mb-8 border border-gold-500/10 shadow-xs"
        >
          <ShieldCheck className="h-3.5 w-3.5 text-gold-500" />
          <span>Every Answer Has a Source You Can Verify</span>
        </motion.div>

        {/* Main Heading */}
        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.0, delay: 0.08, ease: "easeOut" }}
          className="font-serif text-5xl sm:text-6xl md:text-7xl lg:text-[5rem] font-bold leading-[1.05] mb-7 tracking-tight"
        >
          <span className="gradient-warm">Timeless Wisdom,</span>
          <br />
          <span className="text-text-primary">Evidence You Can Trust</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.22, ease: "easeOut" }}
          className="text-base sm:text-lg text-text-secondary max-w-lg mx-auto mb-10 leading-relaxed"
        >
          Thousands of years of Hindu scripture, grounded in evidence.
          Every answer traced to its source. Every claim verifiable.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.35, ease: "easeOut" }}
          className="flex flex-col sm:flex-row items-center justify-center gap-3"
        >
          <Link href="/chat" className="btn-primary text-[15px] px-8 py-3.5 group">
            Begin Your Journey
            <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
          </Link>
          <Link href="/search" className="btn-secondary text-[15px] px-8 py-3.5">
            Explore the Knowledge Base
          </Link>
        </motion.div>

        {/* Stats strip */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.48, ease: "easeOut" }}
          className="mt-20"
        >
          <div className="divider-gold max-w-[200px] mx-auto mb-8" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-lg mx-auto">
            <StatItem value="120K+" label="Verified Chunks" />
            <StatItem value="391" label="Entities" />
            <StatItem value="5K+" label="Relationships" />
            <StatItem value="54" label="Scriptures" />
          </div>
        </motion.div>
      </div>
    </section>
  );
}
