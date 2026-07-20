"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Search, Shield } from "lucide-react";

function StatItem({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <div className="text-2xl sm:text-3xl font-bold text-gold-600 font-serif tracking-tight">
        {value}
      </div>
      <div className="text-xs text-text-tertiary mt-1.5 tracking-wide">{label}</div>
    </div>
  );
}

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Content */}
      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center pt-20">
        {/* Trust badge */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/60 backdrop-blur-sm text-sm text-gold-700 mb-10 border border-gold-500/15 shadow-sm"
        >
          <Shield className="h-3.5 w-3.5" />
          <span>Every Answer Has a Source You Can Verify</span>
        </motion.div>

        {/* Main Heading */}
        <motion.h1
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.15 }}
          className="font-serif text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold leading-[1.1] mb-8 tracking-tight"
        >
          <span className="gradient-warm">Timeless Wisdom</span>
          <br />
          <span className="text-text-primary">Evidence You Can Trust</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="text-base sm:text-lg text-text-secondary max-w-xl mx-auto mb-12 leading-relaxed"
        >
          Explore thousands of years of Hindu scriptures with an AI that
          never guesses. Every answer is traced to canonical sources.
          Every claim has verifiable evidence.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.45 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link
            href="/chat"
            className="btn-primary"
          >
            Begin Your Journey
            <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
          </Link>

          <Link
            href="/search"
            className="btn-secondary"
          >
            <Search className="h-4 w-4 text-text-secondary" />
            Explore the Knowledge Base
          </Link>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="mt-20 pt-8 border-t border-border"
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-2xl mx-auto">
            <StatItem value="120K+" label="Scripture Chunks" />
            <StatItem value="391" label="Entities Mapped" />
            <StatItem value="5K+" label="Relationships" />
            <StatItem value="54" label="Scriptures" />
          </div>
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.8 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 6, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="w-5 h-9 rounded-full border border-border-light flex items-start justify-center p-1"
        >
          <div className="w-1 h-2.5 rounded-full bg-gold-500/50" />
        </motion.div>
      </motion.div>
    </section>
  );
}
