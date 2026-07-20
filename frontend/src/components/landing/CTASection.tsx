"use client";

import Link from "next/link";
import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";

export function CTASection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  return (
    <section className="relative py-32 px-6">
      <div className="max-w-4xl mx-auto text-center" ref={ref}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={inView ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: 0.8 }}
        >
          <div className="glass-strong rounded-3xl p-12 sm:p-16 relative overflow-hidden">
            {/* Background decoration */}
            <div className="absolute inset-0 bg-gradient-to-br from-gold-500/5 via-transparent to-sacred-500/5 pointer-events-none" />
            <div className="absolute top-0 right-0 w-64 h-64 bg-gold-500/5 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-sacred-500/5 rounded-full blur-3xl pointer-events-none" />

            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-sm text-gold-400 mb-8">
                <Sparkles className="h-3.5 w-3.5" />
                <span>Your Journey Begins Here</span>
              </div>

              <h2 className="font-serif text-4xl sm:text-5xl font-bold mb-6">
                Ready to Explore{" "}
                <span className="gradient-gold">Timeless Wisdom</span>?
              </h2>

              <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-10 leading-relaxed">
                No account required. No paywalls. Just thousands of years of
                verified knowledge, ready to answer your questions.
              </p>

              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  href="/chat"
                  className="group inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gold-500 text-surface font-semibold text-lg hover:bg-gold-400 transition-all duration-300 shadow-lg shadow-gold-500/20"
                >
                  Continue Your Journey
                  <ArrowRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" />
                </Link>

                <Link
                  href="/login"
                  className="px-8 py-4 rounded-xl glass text-text-primary font-medium hover:bg-white/10 transition-all duration-300"
                >
                  Sign In (for saved conversations)
                </Link>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
