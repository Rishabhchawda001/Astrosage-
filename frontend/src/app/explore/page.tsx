"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Network, Search, ArrowRight, BookOpen, Users, GitFork, Loader2 } from "lucide-react";
import { Navigation } from "@/components/shared/Navigation";
import { StarField } from "@/components/landing/StarField";
import { graph } from "@/lib/api";
import type { EntityDetail, EntitySummary, GraphStats, PathResult } from "@/types/api";

export default function ExplorePage() {
  const [entityQuery, setEntityQuery] = useState("");
  const [entityResults, setEntityResults] = useState<EntitySummary[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<EntityDetail | null>(null);
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [pathSource, setPathSource] = useState("");
  const [pathTarget, setPathTarget] = useState("");
  const [pathResult, setPathResult] = useState<PathResult | null>(null);

  useEffect(() => {
    graph.stats().then(setStats).catch(() => {});
  }, []);

  const handleEntitySearch = async () => {
    if (!entityQuery.trim()) return;
    setIsLoading(true);
    try {
      const results = await graph.searchEntities(entityQuery, 20);
      setEntityResults(results);
      if (results.length > 0) {
        const detail = await graph.entity(results[0].name);
        setSelectedEntity(detail);
      }
    } catch { /* ignore */ }
    setIsLoading(false);
  };

  const handleSelectEntity = async (name: string) => {
    try {
      const detail = await graph.entity(name);
      setSelectedEntity(detail);
    } catch { /* ignore */ }
  };

  const handlePathSearch = async () => {
    if (!pathSource.trim() || !pathTarget.trim()) return;
    try {
      const result = await graph.path(pathSource, pathTarget);
      setPathResult(result);
    } catch { /* ignore */ }
  };

  return (
    <div className="relative min-h-screen">
      <StarField />
      <Navigation />

      <main className="relative z-10 pt-24 px-4 sm:px-6 pb-16">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-10"
          >
            <h1 className="font-serif text-4xl sm:text-5xl font-bold mb-4">
              Knowledge <span className="gradient-gold">Graph</span>
            </h1>
            <p className="text-text-secondary text-lg">
              Explore 391 entities connected by 5,044 relationships across 54 scriptures
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Left panel: Entity search */}
            <div className="lg:col-span-1 space-y-6">
              {/* Stats */}
              {stats && (
                <div className="glass rounded-2xl p-5">
                  <h3 className="text-sm font-semibold text-text-primary mb-4">Graph Stats</h3>
                  <div className="grid grid-cols-2 gap-4">
                    {[
                      { label: "Entities", value: stats.entities, icon: Users },
                      { label: "Scriptures", value: stats.scriptures, icon: BookOpen },
                      { label: "Edges", value: stats.edges, icon: GitFork },
                      { label: "Edge Types", value: stats.edge_types, icon: Network },
                    ].map((s) => (
                      <div key={s.label} className="text-center">
                        <s.icon className="h-4 w-4 mx-auto text-gold-400 mb-1" />
                        <div className="text-lg font-bold text-gold-400">{s.value}</div>
                        <div className="text-xs text-text-tertiary">{s.label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Entity search */}
              <div className="glass rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-text-primary mb-3">Find Entity</h3>
                <div className="flex gap-2 mb-4">
                  <input
                    type="text"
                    value={entityQuery}
                    onChange={(e) => setEntityQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleEntitySearch()}
                    placeholder="Search entities..."
                    className="flex-1 bg-surface-elevated rounded-xl px-4 py-2.5 text-sm text-text-primary placeholder-text-tertiary border border-border focus:outline-none focus:ring-1 focus:ring-gold-500/30"
                  />
                  <button
                    onClick={handleEntitySearch}
                    disabled={!entityQuery.trim()}
                    className="px-4 py-2.5 rounded-xl bg-gold-500 text-surface text-sm font-semibold hover:bg-gold-400 disabled:opacity-30"
                  >
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                  </button>
                </div>

                <div className="space-y-1 max-h-60 overflow-y-auto">
                  {entityResults.map((e) => (
                    <button
                      key={e.guid}
                      onClick={() => handleSelectEntity(e.name)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                        selectedEntity?.name === e.name
                          ? "bg-gold-500/10 text-gold-400"
                          : "text-text-secondary hover:text-text-primary hover:bg-white/5"
                      }`}
                    >
                      <span className="font-medium">{e.name}</span>
                      <span className="text-xs text-text-tertiary ml-2">({e.type})</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Path finder */}
              <div className="glass rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-text-primary mb-3">Find Path</h3>
                <div className="space-y-2">
                  <input
                    type="text"
                    value={pathSource}
                    onChange={(e) => setPathSource(e.target.value)}
                    placeholder="Source entity..."
                    className="w-full bg-surface-elevated rounded-xl px-4 py-2.5 text-sm text-text-primary placeholder-text-tertiary border border-border focus:outline-none focus:ring-1 focus:ring-gold-500/30"
                  />
                  <input
                    type="text"
                    value={pathTarget}
                    onChange={(e) => setPathTarget(e.target.value)}
                    placeholder="Target entity..."
                    className="w-full bg-surface-elevated rounded-xl px-4 py-2.5 text-sm text-text-primary placeholder-text-tertiary border border-border focus:outline-none focus:ring-1 focus:ring-gold-500/30"
                  />
                  <button
                    onClick={handlePathSearch}
                    disabled={!pathSource.trim() || !pathTarget.trim()}
                    className="w-full px-4 py-2.5 rounded-xl bg-gold-500 text-surface text-sm font-semibold hover:bg-gold-400 disabled:opacity-30"
                  >
                    Find Connection
                  </button>
                </div>
                {pathResult && pathResult.depth > 0 && (
                  <div className="mt-3 p-3 rounded-xl bg-white/5">
                    <p className="text-xs text-gold-400 mb-2">Path found ({pathResult.depth} hops):</p>
                    <div className="flex flex-wrap items-center gap-1">
                      {pathResult.path_names.map((name, i) => (
                        <span key={i} className="flex items-center gap-1">
                          <span className="text-xs text-text-primary">{name}</span>
                          {i < pathResult.path_names.length - 1 && (
                            <ArrowRight className="h-3 w-3 text-text-tertiary" />
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {pathResult && pathResult.depth === 0 && (
                  <p className="mt-3 text-xs text-text-tertiary">No path found between these entities</p>
                )}
              </div>
            </div>

            {/* Right panel: Entity detail */}
            <div className="lg:col-span-2">
              {selectedEntity ? (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass rounded-2xl p-6"
                >
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-gold-400/20 to-gold-600/20 flex items-center justify-center">
                      <Network className="h-7 w-7 text-gold-400" />
                    </div>
                    <div>
                      <h2 className="font-serif text-2xl font-bold text-text-primary">
                        {selectedEntity.name}
                      </h2>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs font-medium text-gold-400 uppercase tracking-wider">
                          {selectedEntity.type}
                        </span>
                        <span className="text-xs text-text-tertiary">·</span>
                        <span className="text-xs text-text-tertiary">
                          {selectedEntity.total_mentions} mentions
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Relationships */}
                  <h3 className="text-sm font-semibold text-text-primary mb-3">
                    Relationships ({selectedEntity.relationships.length})
                  </h3>
                  <div className="space-y-2 max-h-[60vh] overflow-y-auto">
                    {selectedEntity.relationships.map((rel, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-all"
                      >
                        <div className="flex-1 flex items-center gap-2 min-w-0">
                          <span className="text-xs text-text-secondary">
                            {rel.direction === "outgoing" ? "→" : "←"}
                          </span>
                          <span className="text-xs font-medium text-text-primary truncate">
                            {rel.target_name}
                          </span>
                        </div>
                        <span className="text-xs text-gold-400/80 truncate max-w-[200px]">
                          {rel.type}
                        </span>
                        <span className="text-xs text-text-tertiary">
                          {(rel.confidence / 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                    {selectedEntity.relationships.length === 0 && (
                      <p className="text-sm text-text-tertiary py-4 text-center">
                        No relationships found for this entity
                      </p>
                    )}
                  </div>
                </motion.div>
              ) : (
                <div className="glass rounded-2xl p-12 flex flex-col items-center justify-center text-center min-h-[400px]">
                  <Network className="h-16 w-16 text-text-tertiary mb-4" />
                  <h3 className="font-serif text-xl text-text-secondary mb-2">
                    Explore the Knowledge Graph
                  </h3>
                  <p className="text-text-tertiary text-sm max-w-md">
                    Search for an entity to see its relationships, types, and connections
                    across the full knowledge graph.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
