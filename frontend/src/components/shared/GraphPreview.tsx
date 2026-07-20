"use client";

import { useEffect, useRef } from "react";

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
}

export function GraphPreview({ nodes: rawNodes, edges: rawEdges, className = "" }: GraphPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);

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
        x: w / 2 + Math.cos(angle) * w * 0.3,
        y: h / 2 + Math.sin(angle) * h * 0.3,
        vx: 0, vy: 0,
        label: n.name,
        type: n.type,
        radius: n.type === "Scripture" ? 8 : 6,
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

    // Simple force simulation
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
        const target = 60;
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
        node.x = Math.max(20, Math.min(w - 20, node.x));
        node.y = Math.max(20, Math.min(h - 20, node.y));
      }

      // Draw
      ctx.clearRect(0, 0, w, h);

      // Edges
      for (const edge of edges) {
        const a = nodes[edge.from], b = nodes[edge.to];
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = "rgba(240, 176, 0, 0.12)";
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }

      // Nodes
      for (const node of nodes) {
        const typeColor = node.type === "Scripture"
          ? "rgba(100, 180, 255, 0.6)"
          : node.type === "Concept"
            ? "rgba(160, 120, 255, 0.6)"
            : "rgba(240, 176, 0, 0.6)";

        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx.fillStyle = typeColor;
        ctx.fill();

        // Glow
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius * 2.5, 0, Math.PI * 2);
        ctx.fillStyle = typeColor.replace("0.6", "0.08");
        ctx.fill();

        // Label
        ctx.fillStyle = "rgba(240, 240, 245, 0.5)";
        ctx.font = "8px system-ui";
        ctx.textAlign = "center";
        ctx.fillText(node.label, node.x, node.y + node.radius + 10);
      }

      animRef.current = requestAnimationFrame(animate);
    };
    animate();

    return () => cancelAnimationFrame(animRef.current);
  }, [rawNodes, rawEdges]);

  if (rawNodes.length === 0) return null;

  return (
    <canvas
      ref={canvasRef}
      className={`w-full h-full rounded-xl ${className}`}
      aria-hidden="true"
    />
  );
}
