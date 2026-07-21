"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import {
  ShieldCheck, Network,
  Brain, Eye, Quote, Library, Search, FileCheck,
  Scale, Compass
} from "lucide-react";

const stories = [
  {
    icon: Scale,
    title: "Why AstroSage Exists",
    description:
      "In an age of AI that fabricates confidently, AstroSage takes a different path. Every answer is grounded in actual scripture. Every claim has a source you can verify. We believe ancient wisdom deserves modern rigor.",
    gradient: "from-gold-400 to-amber-500",
    span: true,
  },
  {
    icon: ShieldCheck,
    title: "Truth Over Opinion",
    description:
      "AstroSage never fabricates. If the evidence doesn't exist, we say so. Every answer is anchored to canonical scripture — not speculation, not interpretation, not confidence tricks.",
    gradient: "from-amber-400 to-orange-500",
  },
  {
    icon: Brain,
    title: "Evidence Over Hallucination",
    description:
      "Generic AI hallucinates. AstroSage cites. Every claim includes a citation trail: scripture, chapter, verse. You can verify each answer against the original source in seconds.",
    gradient: "from-blue-400 to-purple-500",
  },
  {
    icon: Library,
    title: "Thousands of Scriptures",
    description:
      "54 scriptures. 120,000+ verses. 391 entities. 5,044 relationships. All indexed, cross-referenced, and permanently frozen at v1.0.0 — immutable and auditable.",
    gradient: "from-emerald-500 to-teal-500",
  },
  {
    icon: Network,
    title: "The Knowledge Graph",
    description:
      "Entities aren't just names. They're nodes in a vast, interconnected network. Krishna connects to Arjuna. Arjuna connects to Dharma. Dharma connects to the Bhagavad Gita. Everything is linked.",
    gradient: "from-purple-500 to-pink-500",
  },
  {
    icon: Search,
    title: "How Answers Are Generated",
    description:
      "Your question is expanded with Sanskrit and Hindi synonyms, matched against 120K verified chunks using BM25 search with entity-guided pre-filtering, and assembled into a grounded answer with confidence scoring.",
    gradient: "from-cyan-500 to-blue-500",
  },
  {
    icon: FileCheck,
    title: "Why Hallucinations Are Rejected",
    description:
      "Questions about non-Hindu texts, out-of-domain topics, or entities not in the knowledge graph are immediately detected and rejected with low confidence. We don't guess.",
    gradient: "from-rose-500 to-red-500",
  },
  {
    icon: Eye,
    title: "Verified Citations You Can Trust",
    description:
      "Every answer shows its sources. Hover any citation to see the original scripture text. Every source has a score showing its relevance. Everything is transparent. Nothing is hidden.",
    gradient: "from-amber-400 to-yellow-500",
  },
  {
    icon: Compass,
    title: "Why Trust Matters",
    description:
      "You're exploring thousands of years of philosophical tradition. You deserve answers you can trust. AstroSage is open source, auditable, and built with the highest quality standards — 8/8 quality gates pass before every release.",
    gradient: "from-green-500 to-emerald-500",
    span: true,
  },
];

function StoryCard({
  story,
  index,
}: {
  story: (typeof stories)[0];
  index: number;
}) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.55, delay: index * 0.06, ease: "easeOut" }}
      className={story.span ? "md:col-span-2 lg:col-span-3" : ""}
    >
      <div className="card-premium p-7 sm:p-8 h-full group hover:shadow-lg transition-shadow duration-300">
        <div
          className={`inline-flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-br ${story.gradient} mb-5 shadow-sm`}
        >
          <story.icon className="h-5 w-5 text-white" />
        </div>
        <h3 className="font-serif text-xl font-semibold text-text-primary mb-3 tracking-tight">
          {story.title}
        </h3>
        <p className="text-text-secondary leading-relaxed text-[15px]">
          {story.description}
        </p>
      </div>
    </motion.div>
  );
}

export function StorySection() {
  const titleRef = useRef(null);
  const titleInView = useInView(titleRef, { once: true });

  return (
    <section className="relative py-28 sm:py-32 px-6 bg-surface">
      <div className="max-w-6xl mx-auto">
        {/* Section title */}
        <motion.div
          ref={titleRef}
          initial={{ opacity: 0, y: 30 }}
          animate={titleInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="text-center mb-6"
        >
          <h2 className="font-serif text-4xl sm:text-5xl font-bold mb-4 text-text-primary tracking-tight">
            Built Different by{" "}
            <span className="gradient-warm">Design</span>
          </h2>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
            AstroSage combines modern AI engineering with rigorous scholarly standards.
            Here&apos;s how it works — and why you can trust it.
          </p>
        </motion.div>

        {/* Divider */}
        <motion.div
          initial={{ scaleX: 0 }}
          animate={titleInView ? { scaleX: 1 } : {}}
          transition={{ duration: 0.8, delay: 0.25 }}
          className="h-px bg-gradient-to-r from-transparent via-gold-500/30 to-transparent max-w-xs mx-auto mb-14"
        />

        {/* Story cards grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {stories.map((story, i) => (
            <StoryCard key={story.title} story={story} index={i} />
          ))}
        </div>

        {/* Knowledge base stats strip */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="mt-16 card-premium p-10 sm:p-14 text-center relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-gold-500/[0.04] via-transparent to-sacred-500/[0.04] pointer-events-none" />
          <div className="relative z-10">
            <Quote className="h-7 w-7 mx-auto text-gold-400/35 mb-5" />
            <blockquote className="font-serif text-2xl sm:text-3xl text-text-primary mb-8 leading-relaxed max-w-3xl mx-auto">
              &ldquo;Knowledge is structured in consciousness. AstroSage
              makes that structure visible, verifiable, and eternally
              accessible.&rdquo;
            </blockquote>
            <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-8 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-gold-600 font-serif">120K+</div>
                <div className="text-text-tertiary text-xs mt-1">Verified Chunks</div>
              </div>
              <div className="w-px h-9 bg-border" />
              <div className="text-center">
                <div className="text-2xl font-bold text-gold-600 font-serif">5K+</div>
                <div className="text-text-tertiary text-xs mt-1">Relationships</div>
              </div>
              <div className="w-px h-9 bg-border" />
              <div className="text-center">
                <div className="text-2xl font-bold text-gold-600 font-serif">100%</div>
                <div className="text-text-tertiary text-xs mt-1">Hallucination Rejection</div>
              </div>
              <div className="w-px h-9 bg-border" />
              <div className="text-center">
                <div className="text-2xl font-bold text-gold-600 font-serif">8/8</div>
                <div className="text-text-tertiary text-xs mt-1">Quality Gates</div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
