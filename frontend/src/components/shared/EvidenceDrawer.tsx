"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, BookOpen, ScrollText } from "lucide-react";
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
            className="fixed inset-0 bg-black/40 z-40"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-lg z-50 bg-surface-elevated border-l border-border shadow-2xl"
          >
            <div className="h-full flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-border">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-gold-400" />
                  <h2 className="font-serif text-lg font-semibold">Evidence Source</h2>
                </div>
                <button
                  onClick={closeEvidence}
                  className="p-2 rounded-lg text-text-tertiary hover:text-text-primary hover:bg-white/5 transition-all"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6">
                <div className="space-y-6">
                  {/* Scripture info */}
                  <div className="glass rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <ScrollText className="h-4 w-4 text-gold-400" />
                      <span className="text-sm font-medium text-gold-400">
                        {selectedEvidence.scripture || "Scripture"}
                      </span>
                      <span className="text-xs text-text-tertiary">
                        · {selectedEvidence.level}
                      </span>
                    </div>

                    <p className="text-sm text-text-primary leading-relaxed">
                      {selectedEvidence.text}
                    </p>
                  </div>

                  {/* Score indicator */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-text-tertiary">Relevance Score</span>
                      <span className="text-xs font-medium text-gold-400">
                        {(selectedEvidence.score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-gold-400 to-gold-600"
                        style={{ width: `${selectedEvidence.score * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* Provenance info */}
                  <div className="text-xs text-text-tertiary space-y-1">
                    <p>This evidence was retrieved from the AstroSage knowledge base.</p>
                    <p>
                      Score is calculated using BM25 lexical search with entity-guided
                      pre-filtering and query expansion for Sanskrit/Hindi/English terms.
                    </p>
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
