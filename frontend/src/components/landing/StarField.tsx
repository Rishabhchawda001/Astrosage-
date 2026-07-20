"use client";

import { useEffect, useRef, useCallback } from "react";

interface Star {
  x: number; y: number;
  size: number; opacity: number;
  twinkleSpeed: number; twinklePhase: number;
  layer: number; // 0=deep, 1=mid, 2=near
  hue: number;   // 0=white, 40=gold, 260=sacred
}

interface Particle {
  x: number; y: number;
  vx: number; vy: number;
  size: number; opacity: number;
  hue: number; life: number; maxLife: number;
}

interface Constellation {
  stars: { x: number; y: number }[];
  opacity: number; phase: number; speed: number;
}

export function StarField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const dimsRef = useRef({ w: 0, h: 0 });
  const timeRef = useRef(0);

  const resize = useCallback((canvas: HTMLCanvasElement) => {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = window.innerWidth;
    const h = window.innerHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    dimsRef.current = { w: w * dpr, h: h * dpr };
    return dpr;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let dpr = resize(canvas);
    const { w, h } = dimsRef.current;

    // ── Stars ──
    const starCount = Math.floor((w * h) / 8000);
    const stars: Star[] = Array.from({ length: starCount }, () => ({
      x: Math.random() * w, y: Math.random() * h,
      size: Math.random() * 1.8 + 0.2,
      opacity: Math.random() * 0.7 + 0.3,
      twinkleSpeed: Math.random() * 0.015 + 0.003,
      twinklePhase: Math.random() * Math.PI * 2,
      layer: Math.floor(Math.random() * 3),
      hue: Math.random() > 0.85 ? (Math.random() > 0.5 ? 40 : 260) : 0,
    }));

    // ── Constellations ──
    const constellationCount = 3;
    const constellations: Constellation[] = Array.from({ length: constellationCount }, () => {
      const centerX = Math.random() * w * 0.6 + w * 0.2;
      const centerY = Math.random() * h * 0.4 + h * 0.1;
      const count = 4 + Math.floor(Math.random() * 5);
      return {
        stars: Array.from({ length: count }, () => ({
          x: centerX + (Math.random() - 0.5) * w * 0.15,
          y: centerY + (Math.random() - 0.5) * h * 0.12,
        })),
        opacity: 0,
        phase: Math.random() * Math.PI * 2,
        speed: 0.003 + Math.random() * 0.004,
      };
    });

    // ── Floating particles ──
    let particles: Particle[] = [];

    const spawnParticle = () => {
      if (particles.length < 25) {
        const side = Math.floor(Math.random() * 4);
        particles.push({
          x: side === 0 ? Math.random() * w : side === 1 ? w : side === 2 ? Math.random() * w : 0,
          y: side === 0 ? 0 : side === 1 ? Math.random() * h : side === 2 ? h : Math.random() * h,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3 - 0.1,
          size: Math.random() * 2 + 1,
          opacity: 0,
          hue: Math.random() > 0.5 ? 40 : 260,
          life: 0,
          maxLife: 300 + Math.random() * 400,
        });
      }
    };

    // ── Sacred geometry ──
    const sacredGeo = {
      phase: 0,
      rings: [
        { radius: Math.min(w, h) * 0.12, speed: 0.005, opacity: 0.06 },
        { radius: Math.min(w, h) * 0.18, speed: -0.008, opacity: 0.04 },
        { radius: Math.min(w, h) * 0.24, speed: 0.01, opacity: 0.03 },
        { radius: Math.min(w, h) * 0.30, speed: -0.012, opacity: 0.02 },
      ],
    };

    const cx = w / 2;
    const cy = h / 2;

    const animate = () => {
      timeRef.current += 0.01;
      const t = timeRef.current;
      ctx.clearRect(0, 0, w, h);

      // ── Nebula glow ──
      const nebGrad = ctx.createRadialGradient(cx, cy * 0.4, 0, cx, cy * 0.4, w * 0.5);
      nebGrad.addColorStop(0, "rgba(100, 60, 180, 0.015)");
      nebGrad.addColorStop(0.5, "rgba(60, 30, 120, 0.01)");
      nebGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = nebGrad;
      ctx.fillRect(0, 0, w, h);

      // Secondary nebula
      const nebGrad2 = ctx.createRadialGradient(w * 0.7, h * 0.7, 0, w * 0.7, h * 0.7, w * 0.4);
      nebGrad2.addColorStop(0, "rgba(180, 120, 60, 0.01)");
      nebGrad2.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = nebGrad2;
      ctx.fillRect(0, 0, w, h);

      // ── Sacred geometry ──
      sacredGeo.phase += 0.01;
      for (const ring of sacredGeo.rings) {
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(t * ring.speed);
        ctx.strokeStyle = `rgba(240, 176, 0, ${ring.opacity})`;
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.arc(0, 0, ring.radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      }

      // Flower of Life pattern (simplified)
      const folRadius = Math.min(w, h) * 0.04;
      const folOpacity = 0.03 + Math.sin(t * 0.005) * 0.01;
      for (let i = 0; i < 6; i++) {
        const angle = (i / 6) * Math.PI * 2 + t * 0.003;
        const fx = cx + Math.cos(angle) * folRadius;
        const fy = cy + Math.sin(angle) * folRadius;
        ctx.beginPath();
        ctx.arc(fx, fy, folRadius * 0.6, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(200, 160, 80, ${folOpacity})`;
        ctx.lineWidth = 0.3;
        ctx.stroke();
      }

      // ── Stars ──
      for (const star of stars) {
        const twinkle = Math.sin(t * star.twinkleSpeed * 5 + star.twinklePhase) * 0.3 + 0.7;
        const alpha = star.opacity * twinkle;
        const layerScale = 1 + star.layer * 0.3;

        const color = star.hue === 0
          ? `rgba(255, 255, 255, ${alpha * 0.5 * layerScale})`
          : star.hue === 40
            ? `rgba(255, 200, 100, ${alpha * 0.6 * layerScale})`
            : `rgba(180, 140, 255, ${alpha * 0.6 * layerScale})`;

        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size * layerScale, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        // Glow
        if (star.size > 1.2) {
          ctx.beginPath();
          ctx.arc(star.x, star.y, star.size * 4 * layerScale, 0, Math.PI * 2);
          ctx.fillStyle = star.hue === 0
            ? `rgba(255, 255, 255, ${alpha * 0.04})`
            : `rgba(255, 200, 100, ${alpha * 0.06})`;
          ctx.fill();
        }
      }

      // ── Constellations ──
      for (const con of constellations) {
        con.opacity = Math.sin(t * con.speed + con.phase) * 0.15 + 0.12;
        if (con.opacity > 0.05) {
          ctx.strokeStyle = `rgba(200, 180, 255, ${con.opacity})`;
          ctx.lineWidth = 0.3;
          for (let i = 0; i < con.stars.length - 1; i++) {
            ctx.beginPath();
            ctx.moveTo(con.stars[i].x, con.stars[i].y);
            ctx.lineTo(con.stars[i + 1].x, con.stars[i + 1].y);
            ctx.stroke();
          }
          // Star glows at constellation points
          for (const s of con.stars) {
            ctx.beginPath();
            ctx.arc(s.x, s.y, 1.5, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(200, 180, 255, ${con.opacity * 0.5})`;
            ctx.fill();
          }
        }
      }

      // ── Floating particles ──
      if (Math.random() < 0.02) spawnParticle();
      particles = particles.filter((p) => p.life < p.maxLife);
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.life++;
        p.opacity = Math.sin((p.life / p.maxLife) * Math.PI) * 0.4;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        const pColor = p.hue === 40
          ? `rgba(240, 176, 0, ${p.opacity})`
          : `rgba(160, 120, 255, ${p.opacity})`;
        ctx.fillStyle = pColor;
        ctx.fill();
      }

      animRef.current = requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => {
      dpr = resize(canvas);
    };
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
