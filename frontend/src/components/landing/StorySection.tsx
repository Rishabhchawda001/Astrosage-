"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import {
  ShieldCheck,
  ScrollText,
  Network,
  BookMarked,
  Brain,
  Eye,
  Quote,
  Library,
} from "lucide-react";

const stories = [
  {
    icon: ShieldCheck,
    title: "Truth Over Opinion",
    description:
      "AstroSage never fabricates. Every answer is grounded in actual scripture — not speculation. If the evidence doesn't exist, we say so.",
    gradient: "from-gold-400 to-gold-600",
  },
  {
    icon: Brain,
    title: "Evidence Over Hallucination",
    description:
      "Unlike generic AI, every claim includes a citation trail. You can verify each answer against the original source.",
    gradient: "from-blue-400 to-purple-500",
  },
  {
    icon: Library,
    title: "Thousands of Scriptures",
    description:
      "54 scriptures, 120K+ verses, 391 entities, and 5K+ relationships — indexed, cross-referenced, and ready to explore.",
    gradient: "from-emerald-400 to-teal-500",
  },
  {
    icon: Network,
    title: "The Knowledge Graph",
    description:
      "Entities aren't just names — they're nodes in a vast network of relationships. Explore how Krishna connects to Arjuna, Vishnu, and the cosmos.",
    gradient: "from-purple-400 to-pink-500",
  },
  {
    icon: Eye,
    title: "Verified Citations",
    description:
      "Every answer shows its sources. Hover any citation to see the original scripture text, chapter, and verse.",
    gradient: "from-amber-400 to-orange-500",
  },
  {
    icon: Quote,
    title: "Ancient Wisdom for Modern Questions",
    description:
      "Ask about dharma, karma, moksha, or the nature of reality. Get answers rooted in thousands of years of philosophical tradition.",
    gradient: "from-rose-400 to-red-500",
  },
  {
    icon: ScrollText,
    title: "Scripture-Grounded Reasoning",
    description:
      "Questions like 'What does the Bhagavad Gita say about duty?' produce answers that quote, cite, and explain — not guess.",
    gradient: "from-cyan-400 to-blue-500",
  },
  {
    icon: BookMarked,
    title: "Privacy & Transparency",
    description:
      "Your conversations stay private. No training on your data. No opaque algorithms. Open source, auditable, and trustworthy.",
    gradient: "from-green-400 to-emerald-500",
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
  const inView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 60 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, delay: index * 0.1 }}
      className="group"
    >
      <div className="glass rounded-2xl p-8 h-full hover:bg-white/[0.04] transition-all duration-500">
        <div
          className={`inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br ${story.gradient} mb-5`}
        >
          <story.icon className="h-6 w-6 text-white" />
        </div>
        <h3 className="font-serif text-xl font-semibold text-text-primary mb-3">
          {story.title}
        </h3>
        <p className="text-text-secondary leading-relaxed">{story.description}</p>
      </div>
    </motion.div>
  );
}

export function StorySection() {
  const titleRef = useRef(null);
  const titleInView = useInView(titleRef, { once: true });

  return (
    <section className="relative py-32 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Section title */}
        <motion.div
          ref={titleRef}
          initial={{ opacity: 0, y: 40 }}
          animate={titleInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          className="text-center mb-20"
        >
          <h2 className="font-serif text-4xl sm:text-5xl font-bold mb-4">
            Built Different by{" "}
            <span className="gradient-gold">Design</span>
          </h2>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            AstroSage combines modern AI engineering with rigorous scholarly standards.
            Here&apos;s what makes it unique.
          </p>
        </motion.div>

        {/* Story cards grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {stories.map((story, i) => (
            <StoryCard key={story.title} story={story} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
