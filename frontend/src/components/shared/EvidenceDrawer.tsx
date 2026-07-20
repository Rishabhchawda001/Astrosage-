"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, BookOpen, ScrollText, ShieldCheck, FileCheck, ExternalLink } from "lucide-react";
import { useUIStore } from "@/lib/store";

export function EvidenceDrawer() {
  const { evidenceDrawerOpen, selectedEvidence, closeEvidence } = useUIStore();

  return (
    <AnimatePresence>
      {evidenceDrawerOpen && selectedEvidence && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeEvidence}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 280 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-lg z-50 bg-surface-elevated border-l border-border shadow-2xl"
          >
            <div className="h-full flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-5 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-gold-400/20 to-gold-600/20 flex items-center justify-center">
                    <BookOpen className="h-4 w-4 text-gold-400" />
                  </div>
                  <div>
                    <h2 className="font-serif text-base font-semibold text-text-primary">
                      Evidence Source
                    </h2>
                    <p className="text-[10px] text-text-tertiary tracking-wide">
                      VERIFIED KNOWLEDGE BASE ENTRY
                    </p>
                  </div>
                </div>
                <button
                  onClick={closeEvidence}
                  className="p-2 rounded-lg text-text-tertiary hover:text-text-primary hover:bg-white/5 transition-all"
                  aria-label="Close evidence drawer"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Trust indicator */}
                <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gold-500/5 border border-gold-500/10">
                  <ShieldCheck className="h-4 w-4 text-gold-400" />
                  <span className="text-xs text-gold-400/80 font-medium">
                    This source is retrieved from the frozen v1.0.0 knowledge release
                  </span>
                </div>

                {/* Scripture reference */}
                <div className="glass rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ScrollText className="h-4 w-4 text-gold-400" />
                      <span className="text-sm font-medium text-gold-400">
                        {selectedEvidence.scripture || "Scripture"}
                      </span>
                    </div>
                    <span className="text-[10px] text-text-tertiary uppercase tracking-wider px-2 py-0.5 rounded-md bg-white/5">
                      {selectedEvidence.level}
                    </span>
                  </div>

                  <p className="text-sm text-text-primary leading-relaxed border-l-2 border-gold-500/20 pl-4 italic">
                    &ldquo;{selectedEvidence.text}&rdquo;
                  </p>
                </div>

                {/* Relevance score */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5">
                      <FileCheck className="h-3.5 w-3.5 text-text-tertiary" />
                      <span className="text-xs text-text-tertiary">Relevance to your question</span>
                    </div>
                    <span className="text-xs font-medium text-gold-400 font-mono">
                      {(selectedEvidence.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${selectedEvidence.score * 100}%` }}
                      transition={{ duration: 0.8, ease: "easeOut" }}
                      className="h-full rounded-full bg-gradient-to-r from-gold-500 to-gold-400"
                    />
                  </div>
                  <div className="flex justify-between mt-1.5">
                    <span className="text-[10px] text-text-tertiary">Low relevance</span>
                    <span className="text-[10px] text-text-tertiary">High relevance</span>
                  </div>
                </div>

                {/* Scoring methodology */}
                <div className="text-xs text-text-tertiary space-y-2 leading-relaxed">
                  <p className="font-medium text-text-secondary text-[11px] uppercase tracking-wider">
                    How This Score Is Calculated
                  </p>
                  <p>
                    Relevance is determined by BM25 lexical search with entity-guided
                    pre-filtering and Sanskrit/Hindi/English query expansion. Your
                    question is matched against 120,548 verified chunks from 54 scriptures
                    in the frozen knowledge release (v1.0.0).
                  </p>
                  <p>
                    Only sources with entity matches in the knowledge graph are scored.
                    Adversarial or out-of-domain queries are rejected with low confidence.
                  </p>
                </div>

                {/* Provenance */}
                <div className="border-t border-border pt-4">
                  <div className="flex items-center gap-1.5 mb-2">
                    <ExternalLink className="h-3 w-3 text-text-tertiary" />
                    <span className="text-[10px] text-text-tertiary uppercase tracking-wider font-medium">
                      Provenance
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="text-text-tertiary">Knowledge Version</div>
                    <div className="text-text-secondary text-right font-mono">v1.0.0</div>
                    <div className="text-text-tertiary">Source</div>
                    <div className="text-text-secondary text-right">AstroSage Knowledge Engine</div>
                    <div className="text-text-tertiary">Quality Gate Status</div>
                    <div className="text-text-secondary text-right flex items-center justify-end gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                      8/8 PASS
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
