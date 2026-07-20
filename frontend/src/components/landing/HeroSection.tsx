"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles, BookOpen, Search } from "lucide-react";

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Sacred Geometry Ornaments */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none" aria-hidden="true">
        <div className="relative w-[600px] h-[600px] sm:w-[800px] sm:h-[800px]">
          {/* Outer ring */}
          <div
            className="absolute inset-0 rounded-full border border-white/3 animate-spin"
            style={{ animationDuration: "60s" }}
          />
          {/* Middle ring */}
          <div
            className="absolute inset-[15%] rounded-full border border-white/4"
            style={{ animation: "spin 40s linear infinite reverse" }}
          />
          {/* Inner ring */}
          <div
            className="absolute inset-[30%] rounded-full border border-white/5"
            style={{ animation: "spin 30s linear infinite" }}
          />
          {/* Center glow */}
          <div className="absolute inset-[40%] rounded-full bg-gold-500/5 blur-3xl" />
        </div>
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-sm text-gold-400 mb-8"
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span>Ancient Wisdom, Verified by AI</span>
        </motion.div>

        {/* Main Heading */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="font-serif text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold leading-tight mb-6"
        >
          <span className="gradient-gold">Timeless Wisdom</span>
          <br />
          <span className="text-text-primary">Powered by Evidence</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="text-lg sm:text-xl text-text-secondary max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          Explore thousands of years of Hindu scriptures with an AI that never guesses.
          Every answer is traced to{" "}
          <span className="text-text-primary font-medium">canonical sources</span>.
          Every claim has{" "}
          <span className="text-text-primary font-medium">verifiable evidence</span>.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link
            href="/chat"
            className="group inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gold-500 text-surface font-semibold text-lg hover:bg-gold-400 transition-all duration-300 shadow-lg shadow-gold-500/20"
          >
            Begin Your Journey
            <ArrowRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" />
          </Link>

          <Link
            href="/search"
            className="group inline-flex items-center gap-2 px-8 py-4 rounded-xl glass text-text-primary font-medium text-lg hover:bg-white/10 transition-all duration-300"
          >
            <Search className="h-5 w-5" />
            Explore Knowledge
          </Link>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-8 max-w-3xl mx-auto"
        >
          {[
            { value: "120K+", label: "Scripture Chunks" },
            { value: "391", label: "Entities Mapped" },
            { value: "5K+", label: "Relationships" },
            { value: "54", label: "Scriptures Indexed" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-2xl sm:text-3xl font-bold text-gold-400 font-serif">
                {stat.value}
              </div>
              <div className="text-sm text-text-tertiary mt-1">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="w-6 h-10 rounded-full border-2 border-white/10 flex items-start justify-center p-1.5"
        >
          <div className="w-1.5 h-3 rounded-full bg-gold-500/60" />
        </motion.div>
      </motion.div>
    </section>
  );
}
