"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, BookOpen, ScrollText, ShieldCheck, ExternalLink, Bookmark, BookmarkCheck } from "lucide-react";
import { useUIStore, useBookmarkStore } from "@/lib/store";

export function EvidenceDrawer() {
  const { evidenceDrawerOpen, selectedEvidence, closeEvidence } = useUIStore();
  const { bookmarks, addBookmark, removeBookmark, isBookmarked } = useBookmarkStore();

  return (
    <AnimatePresence>
      {evidenceDrawerOpen && selectedEvidence && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeEvidence}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
          />

          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-md z-50 bg-surface-raised border-l border-border shadow-2xl
                      max-sm:top-auto max-sm:bottom-0 max-sm:left-0 max-sm:max-w-full max-sm:max-h-[85vh] max-sm:rounded-t-3xl max-sm:border-l-0 max-sm:border-t"
          >
            <div className="hidden max-sm:flex justify-center pt-2 pb-1">
              <div className="w-10 h-1 rounded-full bg-text-tertiary/20" />
            </div>
            <div className="h-full flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-5 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-gold-400/15 to-gold-500/15 flex items-center justify-center">
                    <BookOpen className="h-4 w-4 text-gold-600" />
                  </div>
                  <div>
                    <h2 className="font-serif text-base font-semibold text-text-primary">
                      Evidence Source
                    </h2>
                    <p className="text-[10px] text-text-tertiary tracking-wide uppercase">
                      Verified Knowledge Base Entry
                    </p>
                  </div>
                </div>
                <button
                  onClick={closeEvidence}
                  className="p-2 rounded-lg text-text-tertiary hover:text-text-primary hover:bg-warm-100/60 transition-all"
                  aria-label="Close evidence drawer"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-5 space-y-5">
                {/* Trust indicator */}
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-accent-subtle border border-gold-500/10">
                  <ShieldCheck className="h-3.5 w-3.5 text-gold-600" />
                  <span className="text-[11px] text-gold-700/80 font-medium">
                    Retrieved from frozen v1.0.0 knowledge release
                  </span>
                </div>

                {/* Scripture reference */}
                <div className="card p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ScrollText className="h-4 w-4 text-gold-600" />
                      <span className="text-sm font-medium text-gold-700">
                        {selectedEvidence.scripture || "Scripture"}
                      </span>
                    </div>
                    <span className="text-[10px] text-text-tertiary uppercase tracking-wider px-2 py-0.5 rounded-md bg-warm-50">
                      {selectedEvidence.level}
                    </span>
                  </div>

                  <p className="text-sm text-text-primary leading-relaxed border-l-2 border-gold-400/30 pl-4 italic">
                    &ldquo;{selectedEvidence.text}&rdquo;
                  </p>

                  <button
                    onClick={() => {
                      const idx = bookmarks.findIndex(
                        (b) => b.text === selectedEvidence.text && b.scripture === selectedEvidence.scripture
                      );
                      if (idx >= 0) {
                        removeBookmark(idx);
                      } else {
                        addBookmark(selectedEvidence);
                      }
                    }}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      isBookmarked(selectedEvidence)
                        ? "bg-accent-subtle text-gold-700 border border-gold-500/15"
                        : "text-text-tertiary hover:text-text-primary hover:bg-warm-100/60"
                    }`}
                  >
                    {isBookmarked(selectedEvidence) ? (
                      <BookmarkCheck className="h-3 w-3" />
                    ) : (
                      <Bookmark className="h-3 w-3" />
                    )}
                    {isBookmarked(selectedEvidence) ? "Bookmarked" : "Bookmark"}
                  </button>
                </div>

                {/* Relevance score */}
                <div className="card p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] text-text-tertiary uppercase tracking-wider font-medium">
                      Relevance Score
                    </span>
                    <span className="text-sm font-bold text-gold-600">
                      {(selectedEvidence.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full bg-warm-100 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-gold-500 to-gold-400 transition-all duration-500"
                      style={{ width: `${selectedEvidence.score * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-1.5">
                    <span className="text-[10px] text-text-tertiary">Low relevance</span>
                    <span className="text-[10px] text-text-tertiary">High relevance</span>
                  </div>
                </div>

                {/* Scoring methodology */}
                <div className="text-[11px] text-text-tertiary space-y-2 leading-relaxed">
                  <p className="font-medium text-text-secondary text-[11px] uppercase tracking-wider">
                    How This Score Is Calculated
                  </p>
                  <p>
                    Relevance is determined by BM25 lexical search with entity-guided
                    pre-filtering and Sanskrit/Hindi/English query expansion.
                  </p>
                </div>

                {/* Bookmarked sources */}
                {bookmarks.length > 0 && (
                  <div className="border-t border-border pt-4">
                    <div className="flex items-center gap-1.5 mb-3">
                      <BookmarkCheck className="h-3.5 w-3.5 text-gold-500" />
                      <span className="text-[10px] text-text-tertiary uppercase tracking-wider font-medium">
                        Bookmarked ({bookmarks.length})
                      </span>
                    </div>
                    <div className="space-y-1.5 max-h-40 overflow-y-auto">
                      {bookmarks.map((bm, i) => (
                        <div key={i} className="card p-3 group">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5 mb-1">
                                <BookOpen className="h-3 w-3 text-gold-500/50" />
                                <span className="text-[10px] font-medium text-gold-600">
                                  {bm.scripture || "Source"}
                                </span>
                                <span className="text-[10px] text-text-tertiary">
                                  · {(bm.score * 100).toFixed(0)}%
                                </span>
                              </div>
                              <p className="text-[11px] text-text-secondary line-clamp-2 leading-relaxed">
                                {bm.text}
                              </p>
                            </div>
                            <button
                              onClick={() => removeBookmark(i)}
                              className="p-1 rounded-md text-text-tertiary hover:text-red-500 hover:bg-red-50 transition-all opacity-0 group-hover:opacity-100 flex-shrink-0"
                              title="Remove bookmark"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

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
                    <div className="text-text-tertiary">Quality Gate</div>
                    <div className="text-text-secondary text-right flex items-center justify-end gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-success" />
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
