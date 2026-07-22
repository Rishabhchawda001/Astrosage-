"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import {
  ShieldCheck, Network,
  Brain, Eye, Library, Search,
  Scale
} from "lucide-react";

const stories = [
  {
    icon: Scale,
    title: "Why AstroSage Exists",
    description:
      "In an age of AI that fabricates confidently, AstroSage takes a different path. Every answer is grounded in actual scripture. Every claim has a source you can verify.",
    span: true,
  },
  {
    icon: ShieldCheck,
    title: "Truth Over Opinion",
    description:
      "AstroSage never fabricates. If the evidence doesn't exist, we say so. Every answer is anchored to canonical scripture — not speculation, not interpretation.",
  },
  {
    icon: Brain,
    title: "Evidence Over Hallucination",
    description:
      "Generic AI hallucinates. AstroSage cites. Every claim includes a citation trail: scripture, chapter, verse.",
  },
  {
    icon: Library,
    title: "Thousands of Scriptures",
    description:
      "54 scriptures. 120,000+ verses. 391 entities. 5,044 relationships. All indexed and permanently frozen at v1.0.0.",
  },
  {
    icon: Network,
    title: "The Knowledge Graph",
    description:
      "Entities are nodes in a vast, interconnected network. Krishna connects to Arjuna. Arjuna connects to Dharma. Everything is linked.",
  },
  {
    icon: Search,
    title: "How Answers Are Generated",
    description:
      "Your question is expanded with Sanskrit and Hindi synonyms, matched against 120K verified chunks using BM25 search with entity-guided pre-filtering.",
  },
  {
    icon: Eye,
    title: "Verified Citations",
    description:
      "Every answer shows its sources. Hover any citation to see the original scripture text. Everything is transparent.",
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
  const inView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 24 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay: index * 0.05, ease: "easeOut" }}
      className={story.span ? "md:col-span-2 lg:col-span-3" : ""}
    >
      <div className="card-premium p-6 sm:p-7 h-full group">
        <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-gold-400/15 to-gold-500/15 mb-4">
          <story.icon className="h-5 w-5 text-gold-600" />
        </div>
        <h3 className="font-serif text-lg font-semibold text-text-primary mb-2.5 tracking-tight">
          {story.title}
        </h3>
        <p className="text-text-secondary leading-relaxed text-[14px]">
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
      <div className="max-w-5xl mx-auto">
        {/* Section title */}
        <motion.div
          ref={titleRef}
          initial={{ opacity: 0, y: 20 }}
          animate={titleInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="text-center mb-5"
        >
          <h2 className="font-serif text-4xl sm:text-5xl font-bold mb-4 text-text-primary tracking-tight">
            Built Different by{" "}
            <span className="gradient-warm">Design</span>
          </h2>
          <p className="text-lg text-text-secondary max-w-xl mx-auto leading-relaxed">
            AstroSage combines modern AI engineering with rigorous scholarly standards.
            Here&apos;s how it works — and why you can trust it.
          </p>
        </motion.div>

        {/* Divider */}
        <motion.div
          initial={{ scaleX: 0 }}
          animate={titleInView ? { scaleX: 1 } : {}}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="divider-gold max-w-[200px] mx-auto mb-14"
        />

        {/* Story cards grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stories.map((story, i) => (
            <StoryCard key={story.title} story={story} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
