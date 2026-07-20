"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

interface GraphNode {
  x: number; y: number;
  vx: number; vy: number;
  label: string; type: string;
  radius: number;
}

interface GraphEdge {
  from: number; to: number;
  label: string;
}

interface GraphPreviewProps {
  nodes: { name: string; type: string }[];
  edges: { source: string; target: string; type: string }[];
  className?: string;
  onNodeClick?: (name: string) => void;
}

const TYPE_COLORS: Record<string, string> = {
  Scripture: "rgba(100, 180, 255, 0.6)",
  Concept: "rgba(160, 120, 255, 0.6)",
  Entity: "rgba(240, 176, 0, 0.6)",
  Person: "rgba(255, 140, 68, 0.6)",
  Place: "rgba(68, 200, 160, 0.6)",
  Deity: "rgba(255, 200, 50, 0.7)",
};

function getTypeColor(type: string): string {
  return TYPE_COLORS[type] || "rgba(240, 176, 0, 0.6)";
}

export function GraphPreview({ nodes: rawNodes, edges: rawEdges, className = "", onNodeClick }: GraphPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const offsetStart = useRef({ x: 0, y: 0 });
  const hoveredNode = useRef<number | null>(null);
  const nodesRef = useRef<GraphNode[]>([]);
  const edgesRef = useRef<GraphEdge[]>([]);

  // Initialize physics simulation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || rawNodes.length === 0) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const w = rect.width, h = rect.height;

    // Map names to indices
    const nameToIdx = new Map<string, number>();
    rawNodes.forEach((n, i) => nameToIdx.set(n.name.toLowerCase(), i));

    // Create nodes with initial positions in a circle
    const nodes: GraphNode[] = rawNodes.map((n, i) => {
      const angle = (i / rawNodes.length) * Math.PI * 2 - Math.PI / 2;
      return {
        x: w / 2 + Math.cos(angle) * Math.min(w, h) * 0.3,
        y: h / 2 + Math.sin(angle) * Math.min(w, h) * 0.3,
        vx: 0, vy: 0,
        label: n.name,
        type: n.type,
        radius: n.type === "Scripture" ? 8 : n.type === "Deity" ? 7 : 5,
      };
    });

    // Create edges
    const edges: GraphEdge[] = [];
    for (const edge of rawEdges) {
      const si = nameToIdx.get(edge.source.toLowerCase());
      const ti = nameToIdx.get(edge.target.toLowerCase());
      if (si !== undefined && ti !== undefined && si !== ti) {
        edges.push({ from: si, to: ti, label: edge.type });
      }
    }

    nodesRef.current = nodes;
    edgesRef.current = edges;

    const centerX = w / 2, centerY = h / 2;

    const animate = () => {
      // Forces
      for (let i = 0; i < nodes.length; i++) {
        // Center attraction
        nodes[i].vx += (centerX - nodes[i].x) * 0.001;
        nodes[i].vy += (centerY - nodes[i].y) * 0.001;

        // Repulsion between nodes
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = 30 / (dist * dist);
          nodes[i].vx += (dx / dist) * force;
          nodes[i].vy += (dy / dist) * force;
          nodes[j].vx -= (dx / dist) * force;
          nodes[j].vy -= (dy / dist) * force;
        }
      }

      // Spring forces along edges
      for (const edge of edges) {
        const a = nodes[edge.from], b = nodes[edge.to];
        const dx = b.x - a.x, dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const target = 80;
        const force = (dist - target) * 0.005;
        a.vx += (dx / dist) * force;
        a.vy += (dy / dist) * force;
        b.vx -= (dx / dist) * force;
        b.vy -= (dy / dist) * force;
      }

      // Apply velocity with damping
      for (const node of nodes) {
        node.vx *= 0.92;
        node.vy *= 0.92;
        node.x += node.vx;
        node.y += node.vy;
      }

      // Draw
      ctx.clearRect(0, 0, w, h);
      ctx.save();
      ctx.translate(offset.x, offset.y);
      ctx.scale(zoom, zoom);

      // Edges
      for (const edge of edges) {
        const a = nodes[edge.from], b = nodes[edge.to];
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        const isHovered = hoveredNode.current === edge.from || hoveredNode.current === edge.to;
        ctx.strokeStyle = isHovered ? "rgba(240, 176, 0, 0.3)" : "rgba(240, 176, 0, 0.12)";
        ctx.lineWidth = isHovered ? 1 : 0.5;
        ctx.stroke();
      }

      // Nodes
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];
        const isHovered = hoveredNode.current === i;
        const typeColor = getTypeColor(node.type);
        const baseRadius = node.radius * (isHovered ? 1.4 : 1);

        // Glow
        ctx.beginPath();
        ctx.arc(node.x, node.y, baseRadius * 3, 0, Math.PI * 2);
        ctx.fillStyle = typeColor.replace("0.6", isHovered ? "0.15" : "0.08");
        ctx.fill();

        // Node circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, baseRadius, 0, Math.PI * 2);
        ctx.fillStyle = isHovered ? typeColor.replace("0.6", "0.9") : typeColor;
        ctx.fill();

        if (isHovered) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, baseRadius + 1, 0, Math.PI * 2);
          ctx.strokeStyle = "rgba(240, 176, 0, 0.5)";
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }

        // Label (truncated)
        const maxLabelLen = 18;
        const label = node.label.length > maxLabelLen
          ? node.label.slice(0, maxLabelLen) + "…"
          : node.label;
        ctx.fillStyle = isHovered ? "rgba(240, 240, 245, 0.9)" : "rgba(240, 240, 245, 0.5)";
        ctx.font = isHovered ? "bold 9px system-ui" : "8px system-ui";
        ctx.textAlign = "center";
        ctx.fillText(label, node.x, node.y + baseRadius + 12);
      }

      ctx.restore();
      animRef.current = requestAnimationFrame(animate);
    };
    animate();

    return () => cancelAnimationFrame(animRef.current);
  }, [rawNodes, rawEdges, zoom, offset]);

  // Mouse handlers for pan/zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(prev => Math.max(0.3, Math.min(3, prev * delta)));
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true);
      dragStart.current = { x: e.clientX, y: e.clientY };
      offsetStart.current = { ...offset };
    }
  }, [offset]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging) {
      const dx = e.clientX - dragStart.current.x;
      const dy = e.clientY - dragStart.current.y;
      setOffset({
        x: offsetStart.current.x + dx,
        y: offsetStart.current.y + dy,
      });
    } else {
      // Check for node hover
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const mx = (e.clientX - rect.left - offset.x) / zoom;
      const my = (e.clientY - rect.top - offset.y) / zoom;
      let found = -1;
      for (let i = 0; i < nodesRef.current.length; i++) {
        const dx = mx - nodesRef.current[i].x;
        const dy = my - nodesRef.current[i].y;
        if (dx * dx + dy * dy < 400) {
          found = i;
          break;
        }
      }
      hoveredNode.current = found;
      canvas.style.cursor = found >= 0 ? "pointer" : "grab";
    }
  }, [isDragging, zoom, offset]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleClick = useCallback((e: React.MouseEvent) => {
    if (isDragging) return;
    if (!onNodeClick) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left - offset.x) / zoom;
    const my = (e.clientY - rect.top - offset.y) / zoom;
    for (let i = 0; i < nodesRef.current.length; i++) {
      const dx = mx - nodesRef.current[i].x;
      const dy = my - nodesRef.current[i].y;
      if (dx * dx + dy * dy < 400) {
        onNodeClick(nodesRef.current[i].label);
        return;
      }
    }
  }, [isDragging, zoom, offset, onNodeClick]);

  const handleReset = useCallback(() => {
    setZoom(1);
    setOffset({ x: 0, y: 0 });
  }, []);

  if (rawNodes.length === 0) return null;

  return (
    <div className={`relative ${className}`}>
      <canvas
        ref={canvasRef}
        className="w-full h-full rounded-xl"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onClick={handleClick}
        aria-label="Knowledge graph visualization. Scroll to zoom, drag to pan."
        role="img"
      />

      {/* Controls */}
      <div className="absolute bottom-3 right-3 flex items-center gap-1.5">
        <button
          onClick={() => setZoom(prev => Math.min(3, prev * 1.3))}
          className="p-1.5 rounded-lg bg-surface/80 backdrop-blur-sm border border-border/50 text-text-tertiary hover:text-text-primary hover:bg-surface transition-all"
          title="Zoom in"
        >
          <ZoomIn className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={() => setZoom(prev => Math.max(0.3, prev * 0.7))}
          className="p-1.5 rounded-lg bg-surface/80 backdrop-blur-sm border border-border/50 text-text-tertiary hover:text-text-primary hover:bg-surface transition-all"
          title="Zoom out"
        >
          <ZoomOut className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={handleReset}
          className="p-1.5 rounded-lg bg-surface/80 backdrop-blur-sm border border-border/50 text-text-tertiary hover:text-text-primary hover:bg-surface transition-all"
          title="Reset view"
        >
          <RotateCcw className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Zoom level indicator */}
      <div className="absolute top-3 left-3 px-2 py-1 rounded-md bg-surface/60 backdrop-blur-sm border border-border/30 text-[10px] text-text-tertiary font-mono">
        {(zoom * 100).toFixed(0)}%
      </div>
    </div>
  );
}
