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
          initial={{ opacity: 0, y: 16 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          <div className="card-elevated p-10 sm:p-14 relative overflow-hidden">
            {/* Decorative glows */}
            <div className="absolute inset-0 bg-gradient-to-br from-gold-500/[0.02] via-transparent to-transparent pointer-events-none" />
            <div className="absolute top-0 right-0 w-48 h-48 bg-gold-500/[0.03] rounded-full blur-3xl pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-gold-500/[0.02] rounded-full blur-3xl pointer-events-none" />

            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-accent-subtle text-[13px] text-gold-700 mb-6 border border-gold-500/8">
                <Sparkles className="h-3 w-3" />
                <span>Your Journey Begins Here</span>
              </div>

              <h2 className="font-serif text-4xl sm:text-5xl font-bold mb-5 text-text-primary tracking-tight leading-tight">
                Ready to Explore{" "}
                <span className="gradient-warm">Timeless Wisdom</span>?
              </h2>

              <p className="text-lg text-text-secondary max-w-lg mx-auto mb-8 leading-relaxed">
                No account required. No paywalls. Just thousands of years of
                verified knowledge, ready to answer your questions.
              </p>

              <Link
                href="/chat"
                className="group btn-primary text-lg px-9 py-4"
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
