"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Network, Search, ArrowRight, BookOpen, Users, GitFork, Loader2 } from "lucide-react";
import { Navigation } from "@/components/shared/Navigation";
import { StarField } from "@/components/landing/StarField";
import { graph } from "@/lib/api";
import { toast } from "sonner";
import type { EntityDetail, EntitySummary, GraphStats, PathResult } from "@/types/api";
import { GraphPreview } from "@/components/shared/GraphPreview";

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
    graph.stats().then(setStats).catch(() => {
      toast.error("Could not load graph stats");
    });
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
    } catch { toast.error("Entity search failed"); }
    setIsLoading(false);
  };

  const handleSelectEntity = async (name: string) => {
    try {
      const detail = await graph.entity(name);
      setSelectedEntity(detail);
    } catch { toast.error("Failed to load entity details"); }
  };

  const handlePathSearch = async () => {
    if (!pathSource.trim() || !pathTarget.trim()) return;
    try {
      const result = await graph.path(pathSource, pathTarget);
      setPathResult(result);
    } catch { toast.error("Path search failed"); }
  };

  return (
    <div className="relative min-h-screen">
      <StarField />
      <Navigation />

      <main className="relative z-10 pt-24 px-5 sm:px-8 pb-16">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="mb-10"
          >
            <h1 className="font-serif text-4xl sm:text-5xl font-bold mb-4 tracking-tight">
              Knowledge <span className="gradient-gold">Graph</span>
            </h1>
            <p className="text-text-secondary text-lg">
              Explore 391 entities connected by 5,044 relationships across 54 scriptures
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-3 gap-5">
            {/* Left panel */}
            <div className="lg:col-span-1 space-y-5">
              {/* Stats */}
              {stats && (
                <div className="card p-5">
                  <h3 className="text-[13px] font-semibold text-text-primary mb-4">Graph Stats</h3>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: "Entities", value: stats.entities, icon: Users },
                      { label: "Scriptures", value: stats.scriptures, icon: BookOpen },
                      { label: "Edges", value: stats.edges, icon: GitFork },
                      { label: "Edge Types", value: stats.edge_types, icon: Network },
                    ].map((s) => (
                      <div key={s.label} className="text-center p-3 rounded-xl bg-warm-50">
                        <s.icon className="h-4 w-4 mx-auto text-gold-600 mb-1" />
                        <div className="text-lg font-bold text-gold-600">{s.value}</div>
                        <div className="text-[11px] text-text-tertiary">{s.label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Graph Visualization */}
              <div className="card p-5">
                <h3 className="text-[13px] font-semibold text-text-primary mb-3">Graph View</h3>
                <div className="h-48 rounded-xl overflow-hidden bg-warm-50">
                  {selectedEntity ? (
                    <GraphPreview
                      nodes={[
                        { name: selectedEntity.name, type: selectedEntity.type },
                        ...selectedEntity.relationships.slice(0, 15).map((r) => ({
                          name: r.target_name,
                          type: r.target_type || "Entity",
                        })),
                      ]}
                      edges={selectedEntity.relationships.slice(0, 20).map((r) => ({
                        source: selectedEntity.name,
                        target: r.target_name,
                        type: r.type,
                      }))}
                      className="h-full"
                      onNodeClick={handleSelectEntity}
                    />
                  ) : (
                    <div className="h-full flex items-center justify-center">
                      <Network className="h-8 w-8 text-text-tertiary/30" />
                    </div>
                  )}
                </div>
              </div>

              {/* Entity Search */}
              <div className="card p-5">
                <h3 className="text-[13px] font-semibold text-text-primary mb-3">Find Entity</h3>
                <div className="relative mb-3">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary" />
                  <input
                    type="text"
                    value={entityQuery}
                    onChange={(e) => setEntityQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleEntitySearch()}
                    placeholder="e.g., Krishna, Dharma..."
                    className="w-full pl-10 pr-3 py-2.5 rounded-xl bg-warm-50 border border-border text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-1 focus:ring-accent/30 transition-all"
                  />
                </div>
                <button
                  onClick={handleEntitySearch}
                  disabled={!entityQuery.trim() || isLoading}
                  className="w-full py-2 rounded-xl bg-gold-500 text-white text-sm font-semibold hover:bg-gold-400 transition-all disabled:opacity-30 flex items-center justify-center gap-2"
                >
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
                </button>

                {/* Entity results */}
                {entityResults.length > 0 && (
                  <div className="mt-3 space-y-1 max-h-48 overflow-y-auto">
                    {entityResults.map((e) => (
                      <button
                        key={e.guid}
                        onClick={() => handleSelectEntity(e.name)}
                        className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                          selectedEntity?.name === e.name
                            ? "bg-accent-subtle text-gold-700"
                            : "text-text-secondary hover:bg-warm-100/60 hover:text-text-primary"
                        }`}
                      >
                        <span className="font-medium">{e.name}</span>
                        <span className="text-[11px] text-text-tertiary ml-2">{e.type}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Path finder */}
              <div className="card p-5">
                <h3 className="text-[13px] font-semibold text-text-primary mb-3">Find Path</h3>
                <div className="space-y-2">
                  <input
                    type="text"
                    value={pathSource}
                    onChange={(e) => setPathSource(e.target.value)}
                    placeholder="Source entity"
                    className="w-full px-3 py-2 rounded-lg bg-warm-50 border border-border text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-1 focus:ring-accent/30 transition-all"
                  />
                  <input
                    type="text"
                    value={pathTarget}
                    onChange={(e) => setPathTarget(e.target.value)}
                    placeholder="Target entity"
                    className="w-full px-3 py-2 rounded-lg bg-warm-50 border border-border text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-1 focus:ring-accent/30 transition-all"
                  />
                  <button
                    onClick={handlePathSearch}
                    disabled={!pathSource.trim() || !pathTarget.trim()}
                    className="w-full py-2 rounded-xl bg-warm-100 text-text-primary text-sm font-medium hover:bg-warm-200 transition-all disabled:opacity-30 flex items-center justify-center gap-2"
                  >
                    <ArrowRight className="h-3.5 w-3.5" />
                    Find Path
                  </button>
                </div>
                {pathResult && pathResult.depth > 0 && (
                  <div className="mt-3 p-3 rounded-xl bg-warm-50">
                    <p className="text-[11px] text-gold-600 mb-2">Path found ({pathResult.depth} hops):</p>
                    <div className="flex flex-wrap items-center gap-1">
                      {pathResult.path_names.map((name, i) => (
                        <span key={i} className="flex items-center gap-1">
                          <span className="text-xs text-text-primary font-medium">{name}</span>
                          {i < pathResult.path_names.length - 1 && (
                            <ArrowRight className="h-3 w-3 text-text-tertiary" />
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {pathResult && pathResult.depth === 0 && (
                  <p className="mt-3 text-[11px] text-text-tertiary">No path found between these entities</p>
                )}
              </div>
            </div>

            {/* Right panel: Entity detail */}
            <div className="lg:col-span-2">
              {selectedEntity ? (
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                  className="card p-6"
                >
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-gold-400/15 to-gold-500/15 flex items-center justify-center">
                      <Network className="h-6 w-6 text-gold-600" />
                    </div>
                    <div>
                      <h2 className="font-serif text-2xl font-bold text-text-primary tracking-tight">
                        {selectedEntity.name}
                      </h2>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[11px] font-medium text-gold-600 uppercase tracking-wider">
                          {selectedEntity.type}
                        </span>
                        <span className="text-[11px] text-text-tertiary">·</span>
                        <span className="text-[11px] text-text-tertiary">
                          {selectedEntity.total_mentions} mentions
                        </span>
                      </div>
                    </div>
                  </div>

                  <h3 className="text-[13px] font-semibold text-text-primary mb-3">
                    Relationships ({selectedEntity.relationships.length})
                  </h3>
                  <div className="space-y-1.5 max-h-[60vh] overflow-y-auto">
                    {selectedEntity.relationships.map((rel, i) => (
                      <button
                        key={i}
                        onClick={() => handleSelectEntity(rel.target_name)}
                        className="w-full flex items-center gap-3 p-3 rounded-xl bg-warm-50/50 hover:bg-warm-100/80 transition-all text-left group cursor-pointer"
                      >
                        <div className="flex-1 flex items-center gap-2 min-w-0">
                          <span className="text-[11px] text-text-tertiary">
                            {rel.direction === "outgoing" ? "→" : "←"}
                          </span>
                          <span className="text-[13px] font-medium text-text-primary truncate group-hover:text-gold-600 transition-colors">
                            {rel.target_name}
                          </span>
                        </div>
                        <span className="text-[11px] text-gold-600/80 truncate max-w-[200px]">
                          {rel.type}
                        </span>
                        <span className="text-[11px] text-text-tertiary">
                          {(rel.confidence / 100).toFixed(0)}%
                        </span>
                      </button>
                    ))}
                    {selectedEntity.relationships.length === 0 && (
                      <p className="text-sm text-text-tertiary py-4 text-center">
                        No relationships found for this entity
                      </p>
                    )}
                  </div>
                </motion.div>
              ) : (
                <div className="card p-12 flex flex-col items-center justify-center text-center min-h-[400px]">
                  <Network className="h-14 w-14 text-text-tertiary/20 mb-4" />
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
