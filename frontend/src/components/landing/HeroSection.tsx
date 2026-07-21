"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, ShieldCheck } from "lucide-react";

function StatItem({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <div className="text-2xl sm:text-3xl font-bold text-gold-600 font-serif tracking-tight">
        {value}
      </div>
      <div className="text-[11px] sm:text-xs text-text-tertiary mt-1 tracking-wide uppercase">
        {label}
      </div>
    </div>
  );
}

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center pt-24 pb-16">
        {/* Trust badge */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="inline-flex items-center gap-2.5 px-5 py-2 rounded-full bg-white/55 backdrop-blur-md text-sm text-gold-700 mb-8 border border-gold-500/12 shadow-sm"
        >
          <ShieldCheck className="h-4 w-4 text-gold-600" />
          <span className="tracking-wide">Every Answer Has a Source You Can Verify</span>
        </motion.div>

        {/* Main Heading */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.12, ease: "easeOut" }}
          className="font-serif text-5xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-bold leading-[1.08] mb-8 tracking-tight"
        >
          <span className="gradient-warm">Timeless Wisdom,</span>
          <br />
          <span className="text-text-primary">Evidence You Can Trust</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.28, ease: "easeOut" }}
          className="text-base sm:text-lg text-text-secondary max-w-lg mx-auto mb-12 leading-relaxed"
        >
          Thousands of years of Hindu scripture, grounded in evidence.
          Every answer traced to its source. Every claim verifiable.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.42, ease: "easeOut" }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link href="/chat" className="btn-primary text-base px-9 py-4">
            Begin Your Journey
            <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
          </Link>
          <Link href="/search" className="btn-secondary text-base px-9 py-4">
            Explore the Knowledge Base
          </Link>
        </motion.div>

        {/* Stats strip */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.58, ease: "easeOut" }}
          className="mt-20"
        >
          <div className="h-px bg-gradient-to-r from-transparent via-gold-500/25 to-transparent max-w-xs mx-auto mb-10" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-xl mx-auto">
            <StatItem value="120K+" label="Scripture Chunks" />
            <StatItem value="391" label="Entities" />
            <StatItem value="5K+" label="Relationships" />
            <StatItem value="54" label="Scriptures" />
          </div>
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2.0, duration: 0.8 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 6, 0] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
          className="w-5 h-9 rounded-full border border-border-light flex items-start justify-center p-1.5"
        >
          <div className="w-1 h-2.5 rounded-full bg-gold-500/40" />
        </motion.div>
      </motion.div>
    </section>
  );
}
