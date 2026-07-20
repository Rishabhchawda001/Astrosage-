"use client";

import Link from "next/link";
import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";

export function CTASection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  return (
    <section className="relative py-32 px-6 bg-surface">
      <div className="max-w-4xl mx-auto text-center" ref={ref}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={inView ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: 0.8 }}
        >
          <div className="card-premium p-12 sm:p-16 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-gold-500/5 via-transparent to-sacred-500/5 pointer-events-none" />
            <div className="absolute top-0 right-0 w-64 h-64 bg-gold-500/5 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-sacred-500/5 rounded-full blur-3xl pointer-events-none" />

            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gold-500/10 text-sm text-gold-700 mb-8 border border-gold-500/15">
                <Sparkles className="h-3.5 w-3.5" />
                <span>Your Journey Begins Here</span>
              </div>

              <h2 className="font-serif text-4xl sm:text-5xl font-bold mb-6 text-text-primary">
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
