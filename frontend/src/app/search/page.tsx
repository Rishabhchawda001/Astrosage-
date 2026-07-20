"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Search, Loader2, BookOpen, ScrollText, FileText } from "lucide-react";
import { EvidenceDrawer } from "@/components/shared/EvidenceDrawer";
import { Navigation } from "@/components/shared/Navigation";
import { StarField } from "@/components/landing/StarField";
import { search as searchApi, graph } from "@/lib/api";
import { toast } from "sonner";
import { useUIStore } from "@/lib/store";
import type { SearchResult, EntitySummary } from "@/types/api";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [, setEntities] = useState<EntitySummary[]>([]);
  const [activeTab, setActiveTab] = useState<"all" | "entities" | "verses">("all");

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setIsSearching(true);

    try {
      const [searchRes, entityRes] = await Promise.all([
        searchApi.query({ query: query.trim(), top_k: 20 }),
        graph.searchEntities(query.trim(), 10),
      ]);
      setResults(searchRes.results);
      setEntities(entityRes);
    } catch {
      toast.error("Search failed. Please try again.");
    } finally {
      setIsSearching(false);
    }
  }, [query]);

  const filteredResults = activeTab === "all" ? results :
    activeTab === "entities" ? results.filter(r => r.level === "entity") :
    results.filter(r => r.level === "verse");

  return (
    <div className="relative min-h-screen">
      <StarField />
      <Navigation />

      <main className="relative z-10 pt-24 px-4 sm:px-6 pb-16">
        <div className="max-w-4xl mx-auto">
          {/* Hero */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-10"
          >
            <h1 className="font-serif text-4xl sm:text-5xl font-bold mb-4">
              Knowledge <span className="gradient-gold">Search</span>
            </h1>
            <p className="text-text-secondary text-lg max-w-xl mx-auto">
              Explore 120K+ scripture chunks, 391 entities, and 54 scriptures
            </p>
          </motion.div>

          {/* Search bar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="relative mb-8"
          >
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-text-tertiary" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search entities, scriptures, concepts..."
              className="w-full pl-12 pr-4 py-4 rounded-2xl glass text-text-primary placeholder-text-tertiary text-lg focus:outline-none focus:ring-1 focus:ring-gold-500/30 transition-all"
            />
            <button
              onClick={handleSearch}
              disabled={!query.trim() || isSearching}
              className="absolute right-3 top-1/2 -translate-y-1/2 px-5 py-2 rounded-xl bg-gold-500 text-surface text-sm font-semibold hover:bg-gold-400 transition-all disabled:opacity-30"
            >
              {isSearching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Search"
              )}
            </button>
          </motion.div>

          {/* Tabs */}
          {results.length > 0 && (
            <div className="flex gap-2 mb-6">
              {(["all", "entities", "verses"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    activeTab === tab
                      ? "bg-gold-500/10 text-gold-400 border border-gold-500/20"
                      : "text-text-tertiary hover:text-text-primary hover:bg-white/5"
                  }`}
                >
                  {tab === "all" ? "All Results" : tab.charAt(0).toUpperCase() + tab.slice(1)}
                  <span className="ml-1.5 text-xs opacity-60">
                    ({tab === "all" ? results.length :
                      tab === "entities" ? results.filter(r => r.level === "entity").length :
                      results.filter(r => r.level === "verse").length})
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* Results */}
          <div className="space-y-4">
            {filteredResults.map((result, i) => {
                      const evidenceItem = {
                        text: result.text,
                        scripture: result.scripture_id || "",
                        level: result.level,
                        score: result.score,
                      };
                      return (
                        <motion.button
                          key={result.chunk_id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.03 }}
                          onClick={() => useUIStore.getState().openEvidence(evidenceItem)}
                          className="w-full text-left glass rounded-2xl p-5 hover:bg-white/[0.04] transition-all group border border-transparent hover:border-gold-500/10 cursor-pointer"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-gold-400/20 to-gold-600/20 flex items-center justify-center">
                              {result.level === "entity" ? (
                                <BookOpen className="h-5 w-5 text-gold-400" />
                              ) : result.level === "verse" ? (
                                <ScrollText className="h-5 w-5 text-gold-400" />
                              ) : (
                                <FileText className="h-5 w-5 text-gold-400" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-medium text-gold-400 uppercase tracking-wider">
                                  {result.level}
                                </span>
                                {result.scripture_id && (
                                  <>
                                    <span className="text-xs text-text-tertiary">·</span>
                                    <span className="text-xs text-text-tertiary">{result.scripture_id}</span>
                                  </>
                                )}
                                <span className="ml-auto text-xs text-text-tertiary flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-gold-400/40" />
                                  {(result.score * 100).toFixed(0)}%
                                </span>
                              </div>
                              <p className="text-sm text-text-primary leading-relaxed line-clamp-3">
                                {result.text}
                              </p>
                              {result.entity_links.length > 0 && (
                                <div className="flex flex-wrap gap-1.5 mt-2">
                                  {result.entity_links.slice(0, 5).map((link, j) => (
                                    <span
                                      key={j}
                                      className="px-2 py-0.5 rounded-md bg-white/5 text-xs text-text-secondary"
                                    >
                                      {link.name}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </motion.button>
                      );
                    })}

            {results.length > 0 && filteredResults.length === 0 && (
              <div className="text-center py-12">
                <p className="text-text-tertiary">No results in this category</p>
              </div>
            )}

            {!isSearching && query && results.length === 0 && (
              <div className="text-center py-12">
                <Search className="h-12 w-12 mx-auto text-text-tertiary mb-4" />
                <p className="text-text-secondary">No results found for &ldquo;{query}&rdquo;</p>
                <p className="text-text-tertiary text-sm mt-1">Try a different search term</p>
              </div>
            )}
          </div>
        </div>
      </main>
      <EvidenceDrawer />
    </div>
  );
}
