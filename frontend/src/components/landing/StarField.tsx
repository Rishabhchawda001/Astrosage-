"use client";

import { useEffect, useRef, useCallback } from "react";

/* ════════════════════════════════════════════════════════════════
   AstroSage AI — Ambient Background v2.0
   
   Lightweight Canvas 2D for non-home pages.
   Subtle dust particles and soft gradients.
   Pauses when not visible to save mobile battery.
   ════════════════════════════════════════════════════════════════ */

interface Particle {
  x: number; y: number;
  vx: number; vy: number;
  size: number; opacity: number;
  life: number; maxLife: number;
}

export function StarField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const isVisible = useRef(true);

  const resize = useCallback((canvas: HTMLCanvasElement) => {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = window.innerWidth;
    const h = window.innerHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    return { w: w * dpr, h: h * dpr };
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { isVisible.current = entry.isIntersecting; },
      { threshold: 0.1 }
    );
    if (canvasRef.current) observer.observe(canvasRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let dims = resize(canvas);
    let t = 0;

    let particles: Particle[] = [];
    const spawnParticle = () => {
      if (particles.length < 15) {
        particles.push({
          x: Math.random() * dims.w,
          y: Math.random() * dims.h,
          vx: (Math.random() - 0.5) * 0.12,
          vy: (Math.random() - 0.5) * 0.12 - 0.04,
          size: 0.3 + Math.random() * 0.8,
          opacity: 0,
          life: 0,
          maxLife: 500 + Math.random() * 500,
        });
      }
    };

    const animate = () => {
      if (!isVisible.current) {
        animRef.current = requestAnimationFrame(animate);
        return;
      }

      t++;
      dims = resize(canvas);
      const { w, h } = dims;
      ctx.clearRect(0, 0, w, h);

      // Very subtle warm gradient
      const bg = ctx.createRadialGradient(w * 0.5, h * 0.3, 0, w * 0.5, h * 0.5, w * 0.7);
      bg.addColorStop(0, "rgba(254, 253, 251, 0.01)");
      bg.addColorStop(1, "rgba(254, 253, 251, 0)");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, w, h);

      // Sparse floating particles
      if (Math.random() < 0.008) spawnParticle();
      particles = particles.filter(p => p.life < p.maxLife);

      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.life++;
        p.opacity = Math.sin((p.life / p.maxLife) * Math.PI) * 0.15;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(212, 168, 74, ${p.opacity})`;
        ctx.fill();
      }

      animRef.current = requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => { resize(canvas); };
    window.addEventListener("resize", handleResize);
    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener("resize", handleResize);
    };
  }, [resize]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none select-none"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    />
  );
}
