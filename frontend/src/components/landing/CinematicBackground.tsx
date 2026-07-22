"use client";

import { useEffect, useRef, useCallback } from "react";

/* ════════════════════════════════════════════════════════════════
   AstroSage AI — Live Hero Background v2.0
   
   GPU-accelerated Canvas 2D rendering at 60fps.
   Represents Sanātana Dharma through abstract environmental elements:
   - Sacred geometry (Sri Yantra-inspired concentric patterns)
   - Flowing river geometry (gentle sine waves)
   - Lotus particle movement (petal-shaped particles)
   - Mountain silhouette mist
   - Light rays from above
   - Floating dust/pollen particles
   - Gentle clouds
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
  type: "dust" | "petal" | "pollen";
}

export function CinematicBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const raf = useRef<number>(0);

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

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    const ctx = c.getContext("2d", { alpha: true })!;
    let W = c.width;
    let H = c.height;
    let t = 0;

    /* ── Particles ── */
    let particles: Particle[] = [];

    function spawnParticle() {
      if (particles.length > 40) return;
      const types: Particle["type"][] = ["dust", "petal", "pollen"];
      const type = types[Math.floor(Math.random() * types.length)];
      particles.push({
        x: Math.random() * W,
        y: H * 0.2 + Math.random() * H * 0.6,
        sz: type === "petal" ? 1.5 + Math.random() * 2 : 0.3 + Math.random() * 1.0,
        op: 0,
        vx: (Math.random() - 0.5) * 0.04,
        vy: -(0.01 + Math.random() * 0.03),
        ph: Math.random() * Math.PI * 2,
        life: 0,
        max: 300 + Math.random() * 400,
        type,
      });
    }

    /* ── Soft gradient background ── */
    function drawBackground() {
      const g = ctx.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0, "rgba(254, 253, 251, 0.02)");
      g.addColorStop(0.3, "rgba(250, 248, 245, 0.01)");
      g.addColorStop(0.7, "rgba(245, 243, 239, 0.02)");
      g.addColorStop(1, "rgba(254, 253, 251, 0.04)");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
    }

    /* ── Sacred geometry (subtle concentric patterns) ── */
    function drawSacredGeometry() {
      const cx = W * 0.5;
      const cy = H * 0.42;
      const baseRadius = Math.min(W, H) * 0.12;

      ctx.save();
      ctx.globalAlpha = 0.025 + Math.sin(t * 0.0003) * 0.005;

      // Concentric circles
      for (let i = 0; i < 5; i++) {
        const r = baseRadius * (0.4 + i * 0.25);
        const rotation = t * 0.0001 * (i % 2 === 0 ? 1 : -1);
        
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(212, 168, 74, ${0.3 - i * 0.05})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();

        // Inner petal pattern (lotus-inspired)
        if (i < 3) {
          const petalCount = 8 + i * 4;
          for (let j = 0; j < petalCount; j++) {
            const angle = (j / petalCount) * Math.PI * 2 + rotation;
            const px = cx + Math.cos(angle) * r * 0.85;
            const py = cy + Math.sin(angle) * r * 0.85;
            const pr = r * 0.06;

            ctx.beginPath();
            ctx.ellipse(px, py, pr, pr * 0.4, angle, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(212, 168, 74, ${0.15 - i * 0.03})`;
            ctx.fill();
          }
        }
      }

      ctx.restore();
    }

    /* ── Flowing river geometry (gentle sine waves) ── */
    function drawRiver() {
      ctx.save();
      ctx.globalAlpha = 0.02;

      for (let i = 0; i < 3; i++) {
        const baseY = H * (0.55 + i * 0.08);
        ctx.beginPath();
        ctx.moveTo(0, baseY);

        for (let x = 0; x <= W; x += 4) {
          const y = baseY + 
            Math.sin(x * 0.003 + t * 0.0004 + i * 0.5) * 15 +
            Math.sin(x * 0.007 + t * 0.0002) * 8;
          ctx.lineTo(x, y);
        }

        ctx.strokeStyle = `rgba(212, 168, 74, ${0.4 - i * 0.1})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }

      ctx.restore();
    }

    /* ── Mountain silhouette ── */
    function drawMountains() {
      ctx.save();
      ctx.globalAlpha = 0.015;

      // Far mountains
      ctx.beginPath();
      ctx.moveTo(0, H * 0.85);
      ctx.lineTo(W * 0.15, H * 0.72);
      ctx.lineTo(W * 0.25, H * 0.76);
      ctx.lineTo(W * 0.4, H * 0.65);
      ctx.lineTo(W * 0.5, H * 0.70);
      ctx.lineTo(W * 0.6, H * 0.62);
      ctx.lineTo(W * 0.75, H * 0.74);
      ctx.lineTo(W * 0.85, H * 0.68);
      ctx.lineTo(W, H * 0.80);
      ctx.lineTo(W, H);
      ctx.lineTo(0, H);
      ctx.closePath();
      ctx.fillStyle = "rgba(44, 36, 24, 0.4)";
      ctx.fill();

      // Near mountains
      ctx.beginPath();
      ctx.moveTo(0, H * 0.90);
      ctx.lineTo(W * 0.2, H * 0.82);
      ctx.lineTo(W * 0.35, H * 0.86);
      ctx.lineTo(W * 0.55, H * 0.78);
      ctx.lineTo(W * 0.7, H * 0.84);
      ctx.lineTo(W * 0.9, H * 0.80);
      ctx.lineTo(W, H * 0.88);
      ctx.lineTo(W, H);
      ctx.lineTo(0, H);
      ctx.closePath();
      ctx.fillStyle = "rgba(44, 36, 24, 0.25)";
      ctx.fill();

      ctx.restore();
    }

    /* ── Light rays ── */
    function drawRays() {
      const sx = W * 0.5;
      const sy = H * 0.1;
      ctx.save();
      ctx.globalAlpha = 0.012 + Math.sin(t * 0.0002) * 0.004;

      for (let i = 0; i < 8; i++) {
        const a = (i / 8) * Math.PI * 0.4 - 0.2 + Math.PI * 0.3;
        const len = H * 0.7;
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(
          sx + Math.cos(a - 0.006) * len,
          sy + Math.sin(a - 0.006) * len
        );
        ctx.lineTo(
          sx + Math.cos(a + 0.006) * len,
          sy + Math.sin(a + 0.006) * len
        );
        ctx.closePath();
        const rg = ctx.createLinearGradient(sx, sy, sx + Math.cos(a) * len, sy + Math.sin(a) * len);
        rg.addColorStop(0, "rgba(255,235,190,0.3)");
        rg.addColorStop(0.3, "rgba(255,225,170,0.08)");
        rg.addColorStop(1, "rgba(255,215,150,0)");
        ctx.fillStyle = rg;
        ctx.fill();
      }
      ctx.restore();
    }

    /* ── Atmospheric particles ── */
    function drawParticles() {
      if (Math.random() < 0.015) spawnParticle();
      particles = particles.filter((d) => d.life < d.max);

      for (const d of particles) {
        d.x += d.vx + Math.sin(t * 0.0003 + d.ph) * 0.02;
        d.y += d.vy;
        d.life++;

        const fi = Math.min(d.life / 50, 1);
        const fo = Math.max(0, 1 - (d.life - d.max + 60) / 60);
        d.op = fi * fo * (d.type === "petal" ? 0.12 : 0.08);

        if (d.y < 0) d.op *= 0.1;

        ctx.beginPath();

        if (d.type === "petal") {
          // Lotus petal shape
          const angle = Math.atan2(d.vy, d.vx);
          ctx.save();
          ctx.translate(d.x, d.y);
          ctx.rotate(angle + Math.sin(t * 0.001 + d.ph) * 0.3);
          ctx.ellipse(0, 0, d.sz * 1.5, d.sz * 0.6, 0, 0, Math.PI * 2);
          ctx.restore();
          ctx.fillStyle = `rgba(212, 168, 74, ${d.op})`;
        } else if (d.type === "pollen") {
          ctx.arc(d.x, d.y, d.sz * 0.7, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(235, 208, 138, ${d.op})`;
        } else {
          ctx.arc(d.x, d.y, d.sz, 0, Math.PI * 2);
          const w = Math.sin(t * 0.0003 + d.ph) * 0.5 + 0.5;
          ctx.fillStyle = `rgba(${200 + w * 35}, ${190 + w * 25}, ${170 + w * 15}, ${d.op})`;
        }

        ctx.fill();
      }
    }

    /* ── Gentle mist at bottom ── */
    function drawMist() {
      const my = H * 0.7;
      const g = ctx.createLinearGradient(0, my, 0, H);
      g.addColorStop(0, "rgba(254,253,251,0)");
      g.addColorStop(0.15, "rgba(254,253,251,0.02)");
      g.addColorStop(0.4, "rgba(254,253,251,0.08)");
      g.addColorStop(0.7, "rgba(254,253,251,0.3)");
      g.addColorStop(1, "rgba(254,253,251,0.85)");
      ctx.fillStyle = g;
      ctx.fillRect(0, my, W, H - my);
    }

    /* ── Soft vignette ── */
    function drawVignette() {
      ctx.save();
      ctx.globalAlpha = 0.04;
      const vg = ctx.createRadialGradient(W * 0.5, H * 0.42, W * 0.2, W * 0.5, H * 0.5, W * 0.8);
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

      drawBackground();

      if (!prefersReducedMotion) {
        drawSacredGeometry();
        drawRiver();
        drawRays();
        drawParticles();
      }

      drawMountains();
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
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none select-none"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    />
  );
}
