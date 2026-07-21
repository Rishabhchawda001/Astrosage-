"use client";

import Link from "next/link";
import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";

export function CTASection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });

  return (
    <section className="relative py-28 sm:py-32 px-6 bg-surface">
      <div className="max-w-4xl mx-auto text-center" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: "easeOut" }}
        >
          <div className="card-premium p-12 sm:p-16 relative overflow-hidden">
            {/* Decorative glows */}
            <div className="absolute inset-0 bg-gradient-to-br from-gold-500/[0.04] via-transparent to-sacred-500/[0.04] pointer-events-none" />
            <div className="absolute top-0 right-0 w-56 h-56 bg-gold-500/[0.04] rounded-full blur-3xl pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-56 h-56 bg-sacred-500/[0.04] rounded-full blur-3xl pointer-events-none" />

            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gold-500/[0.08] text-sm text-gold-700 mb-8 border border-gold-500/12">
                <Sparkles className="h-3.5 w-3.5" />
                <span className="tracking-wide">Your Journey Begins Here</span>
              </div>

              <h2 className="font-serif text-4xl sm:text-5xl font-bold mb-6 text-text-primary tracking-tight leading-tight">
                Ready to Explore{" "}
                <span className="gradient-warm">Timeless Wisdom</span>?
              </h2>

              <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-10 leading-relaxed">
                No account required. No paywalls. Just thousands of years of
                verified knowledge, ready to answer your questions.
              </p>

              <Link
                href="/chat"
                className="group btn-primary text-lg px-10 py-5"
              >
                Continue Your Journey
                <ArrowRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" />
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
