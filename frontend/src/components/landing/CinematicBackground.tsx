"use client";

import { useEffect, useRef, useCallback } from "react";

/* ════════════════════════════════════════════════════════════════
   AstroSage AI — Cinematic Hero Background
   Generated artwork + subtle atmospheric canvas overlay
   ════════════════════════════════════════════════════════════════ */

interface Particle {
  x: number;
  y: number;
  sz: number;
  op: number;
  vx: number;
  vy: number;
  ph: number;
  life: number;
  max: number;
}

export function CinematicBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const raf = useRef<number>(0);
  const imgRef = useRef<HTMLImageElement | null>(null);
  const imgLoaded = useRef(false);

  const getSize = useCallback((c: HTMLCanvasElement) => {
    const d = Math.min(window.devicePixelRatio || 1, 2);
    const w = window.innerWidth;
    const h = window.innerHeight;
    c.width = w * d;
    c.height = h * d;
    c.style.width = `${w}px`;
    c.style.height = `${h}px`;
    return d;
  }, []);

  useEffect(() => {
    const c = canvasRef.current;
    if (!c) return;

    /* Check reduced-motion preference */
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    const ctx = c.getContext("2d")!;
    let W = c.width;
    let H = c.height;
    let t = 0;

    /* Load hero artwork */
    const img = new Image();
    img.src = "/hero-artwork/v3_painterly_tradition.jpg";
    img.onload = () => {
      imgRef.current = img;
      imgLoaded.current = true;
    };

    /* ── Particles ── */
    let particles: Particle[] = [];

    function spawnParticle() {
      particles.push({
        x: Math.random() * W,
        y: H * 0.15 + Math.random() * H * 0.65,
        sz: 0.4 + Math.random() * 1.2,
        op: 0,
        vx: (Math.random() - 0.5) * 0.06,
        vy: -(0.015 + Math.random() * 0.04),
        ph: Math.random() * Math.PI * 2,
        life: 0,
        max: 280 + Math.random() * 320,
      });
    }

    /* ── Draw artwork ── */
    function drawArtwork() {
      if (!imgRef.current || !imgLoaded.current) return;
      const img = imgRef.current;
      const imgAspect = img.width / img.height;
      const canvasAspect = W / H;

      let dw: number, dh: number, dx: number, dy: number;

      if (canvasAspect > imgAspect) {
        /* Canvas is wider — fill width, crop height */
        dw = W;
        dh = W / imgAspect;
        dx = 0;
        dy = (H - dh) / 2;
      } else {
        /* Canvas is taller — fill height, crop width */
        dh = H;
        dw = H * imgAspect;
        dx = (W - dw) / 2;
        dy = 0;
      }

      ctx.drawImage(img, dx, dy, dw, dh);
    }

    /* ── Subtle light rays ── */
    function drawRays() {
      const sx = W * 0.57;
      const sy = H * 0.38;
      ctx.save();
      ctx.globalAlpha = 0.018 + Math.sin(t * 0.00025) * 0.005;
      for (let i = 0; i < 12; i++) {
        const a = (i / 12) * Math.PI * 0.65 - 0.12;
        const len = H * 0.85;
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(
          sx + Math.cos(a - 0.008) * len,
          sy + Math.sin(a - 0.008) * len
        );
        ctx.lineTo(
          sx + Math.cos(a + 0.008) * len,
          sy + Math.sin(a + 0.008) * len
        );
        ctx.closePath();
        const rg = ctx.createLinearGradient(
          sx,
          sy,
          sx + Math.cos(a) * len,
          sy + Math.sin(a) * len
        );
        rg.addColorStop(0, "rgba(255,225,160,0.35)");
        rg.addColorStop(0.25, "rgba(255,215,140,0.12)");
        rg.addColorStop(1, "rgba(255,205,120,0)");
        ctx.fillStyle = rg;
        ctx.fill();
      }
      ctx.restore();
    }

    /* ── Atmospheric particles ── */
    function drawParticles() {
      if (Math.random() < 0.012) spawnParticle();
      particles = particles.filter((d) => d.life < d.max);

      for (const d of particles) {
        d.x += d.vx + Math.sin(t * 0.0004 + d.ph) * 0.03;
        d.y += d.vy;
        d.life++;

        const fi = Math.min(d.life / 60, 1);
        const fo = Math.max(0, 1 - (d.life - d.max + 70) / 70);
        d.op = fi * fo * 0.10;

        if (d.y < 0) d.op *= 0.1;

        ctx.beginPath();
        ctx.arc(d.x, d.y, d.sz, 0, Math.PI * 2);
        const w = Math.sin(t * 0.0004 + d.ph) * 0.5 + 0.5;
        ctx.fillStyle = `rgba(${215 + w * 35},${195 + w * 25},${155 + w * 15},${d.op})`;
        ctx.fill();
      }
    }

    /* ── Gentle mist at bottom ── */
    function drawMist() {
      const my = H * 0.72;
      const g = ctx.createLinearGradient(0, my, 0, H);
      g.addColorStop(0, "rgba(248,246,242,0)");
      g.addColorStop(0.20, "rgba(248,246,242,0.04)");
      g.addColorStop(0.50, "rgba(248,246,242,0.15)");
      g.addColorStop(0.80, "rgba(248,246,242,0.50)");
      g.addColorStop(1, "rgba(248,246,242,0.92)");
      ctx.fillStyle = g;
      ctx.fillRect(0, my, W, H - my);
    }

    /* ── Soft vignette ── */
    function drawVignette() {
      ctx.save();
      ctx.globalAlpha = 0.06;
      const vg = ctx.createRadialGradient(
        W * 0.5,
        H * 0.42,
        W * 0.22,
        W * 0.5,
        H * 0.5,
        W * 0.78
      );
      vg.addColorStop(0, "rgba(0,0,0,0)");
      vg.addColorStop(1, "rgba(0,0,0,1)");
      ctx.fillStyle = vg;
      ctx.fillRect(0, 0, W, H);
      ctx.restore();
    }

    /* ════════════════════════════════════════════════════════════
       MAIN LOOP
       ════════════════════════════════════════════════════════════ */
    const animate = () => {
      t++;
      W = c.width;
      H = c.height;
      ctx.clearRect(0, 0, W, H);

      /* Background: artwork image */
      drawArtwork();

      if (!prefersReducedMotion) {
        /* Atmospheric overlays — only when motion is allowed */
        drawRays();
        drawParticles();
      }

      /* Always draw mist and vignette for readability */
      drawMist();
      drawVignette();

      raf.current = requestAnimationFrame(animate);
    };
    animate();

    const onResize = () => {
      getSize(c);
      W = c.width;
      H = c.height;
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf.current);
      window.removeEventListener("resize", onResize);
    };
  }, [getSize]);

  return (
    <>
      {/* Static image layer — immediate display, no canvas jank on load */}
      <div
        className="fixed inset-0 w-full h-full"
        style={{
          zIndex: 0,
          backgroundImage: "url(/hero-artwork/v3_painterly_tradition.jpg)",
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundColor: "#e8e0d0",
        }}
        aria-hidden="true"
      />

      {/* Canvas overlay for atmospheric effects */}
      <canvas
        ref={canvasRef}
        className="fixed inset-0 w-full h-full pointer-events-none select-none"
        style={{ zIndex: 1 }}
        aria-hidden="true"
      />
    </>
  );
}
