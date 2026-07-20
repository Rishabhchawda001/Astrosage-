"use client";

import { useEffect, useRef, useCallback } from "react";

interface Cloud {
  x: number;
  y: number;
  width: number;
  height: number;
  speed: number;
  opacity: number;
}

interface MountainRange {
  peaks: { x: number; y: number }[];
  color: string;
  parallax: number;
}

interface Particle {
  x: number;
  y: number;
  size: number;
  opacity: number;
  driftX: number;
  driftSpeed: number;
  phase: number;
}

export function CinematicBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);

  const resize = useCallback((canvas: HTMLCanvasElement) => {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = window.innerWidth;
    const h = window.innerHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    return dpr;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let dpr = resize(canvas);

    const ctx = canvas.getContext("2d")!;
    let t = 0;

    // ── Generate mountain ranges ──
    function genMountainRange(
      baseY: number,
      numPeaks: number,
      w: number,
      h: number
    ): { x: number; y: number }[] {
      const peaks: { x: number; y: number }[] = [];
      for (let i = 0; i <= numPeaks; i++) {
        peaks.push({
          x: (i / numPeaks) * w * dpr,
          y:
            baseY * h * dpr +
            (Math.random() - 0.5) * h * dpr * 0.08 -
            Math.sin((i / numPeaks) * Math.PI) * h * dpr * 0.04,
        });
      }
      return peaks;
    }

    const farMountains: MountainRange = {
      peaks: [],
      color: "rgba(140, 130, 120, 0.25)",
      parallax: 0.003,
    };
    const midMountains: MountainRange = {
      peaks: [],
      color: "rgba(100, 90, 80, 0.35)",
      parallax: 0.006,
    };
    const nearMountains: MountainRange = {
      peaks: [],
      color: "rgba(70, 62, 55, 0.45)",
      parallax: 0.01,
    };

    function initMountains() {
      const w = canvas!.width;
      const h = canvas!.height;
      farMountains.peaks = genMountainRange(0.62, 12, w, h);
      midMountains.peaks = genMountainRange(0.68, 10, w, h);
      nearMountains.peaks = genMountainRange(0.74, 8, w, h);
    }
    initMountains();

    // ── Generate clouds ──
    const clouds: Cloud[] = [];
    for (let i = 0; i < 6; i++) {
      clouds.push({
        x: Math.random() * 2 - 0.5,
        y: 0.15 + Math.random() * 0.2,
        width: 0.12 + Math.random() * 0.15,
        height: 0.02 + Math.random() * 0.02,
        speed: 0.00003 + Math.random() * 0.00004,
        opacity: 0.12 + Math.random() * 0.15,
      });
    }

    // ── Floating particles (dust motes in sunlight) ──
    let particles: Particle[] = [];
    function spawnParticle() {
      const w = canvas!.width;
      const h = canvas!.height;
      particles.push({
        x: Math.random() * w,
        y: h * 0.4 + Math.random() * h * 0.4,
        size: 1 + Math.random() * 2,
        opacity: 0,
        driftX: (Math.random() - 0.5) * 0.15,
        driftSpeed: 0.08 + Math.random() * 0.12,
        phase: Math.random() * Math.PI * 2,
      });
    }

    // ── Draw functions ──

    function drawSky(w: number, h: number) {
      const grad = ctx.createLinearGradient(0, 0, 0, h);
      // Top: soft warm gray-blue → middle: warm ivory → horizon: warm gold
      grad.addColorStop(0, "#c8bfb4");
      grad.addColorStop(0.3, "#e0d8cc");
      grad.addColorStop(0.55, "#ede6d8");
      grad.addColorStop(0.7, "#f0e0c0");
      grad.addColorStop(0.85, "#e8c888");
      grad.addColorStop(1.0, "#d4a050");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);
    }

    function drawSun(w: number, h: number) {
      const sunX = w * 0.65;
      const sunY = h * 0.62;
      const sunR = Math.min(w, h) * 0.06;

      // Outer glow
      const glow = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, sunR * 5);
      glow.addColorStop(0, "rgba(255, 210, 120, 0.25)");
      glow.addColorStop(0.4, "rgba(255, 200, 100, 0.10)");
      glow.addColorStop(1, "rgba(255, 180, 80, 0)");
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, w, h);

      // Sun disc
      const sunGrad = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, sunR);
      sunGrad.addColorStop(0, "rgba(255, 220, 140, 0.9)");
      sunGrad.addColorStop(0.6, "rgba(255, 200, 110, 0.6)");
      sunGrad.addColorStop(1, "rgba(255, 180, 80, 0)");
      ctx.fillStyle = sunGrad;
      ctx.beginPath();
      ctx.arc(sunX, sunY, sunR, 0, Math.PI * 2);
      ctx.fill();
    }

    function drawLightRays(w: number, h: number) {
      const sunX = w * 0.65;
      const sunY = h * 0.62;
      ctx.save();
      ctx.globalAlpha = 0.04 + Math.sin(t * 0.0005) * 0.01;
      for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 0.6 - 0.1;
        const rayLen = h * 0.8;
        ctx.beginPath();
        ctx.moveTo(sunX, sunY);
        ctx.lineTo(
          sunX + Math.cos(angle - 0.015) * rayLen,
          sunY + Math.sin(angle - 0.015) * rayLen
        );
        ctx.lineTo(
          sunX + Math.cos(angle + 0.015) * rayLen,
          sunY + Math.sin(angle + 0.015) * rayLen
        );
        ctx.closePath();
        ctx.fillStyle = "rgba(255, 220, 140, 0.5)";
        ctx.fill();
      }
      ctx.restore();
    }

    function drawMountains(range: MountainRange, w: number, h: number) {
      const offset = t * range.parallax;
      ctx.beginPath();
      ctx.moveTo(-10, h);
      for (const peak of range.peaks) {
        const x = ((peak.x + offset) % (w + 100)) - 50;
        ctx.lineTo(x, peak.y);
      }
      ctx.lineTo(w + 10, h);
      ctx.closePath();
      ctx.fillStyle = range.color;
      ctx.fill();
    }

    function drawClouds(w: number, h: number) {
      for (const cloud of clouds) {
        cloud.x += cloud.speed;
        if (cloud.x > 1.3) cloud.x = -cloud.width - 0.1;

        const cx = cloud.x * w;
        const cy = cloud.y * h;
        const cw = cloud.width * w;
        const ch = cloud.height * h;

        ctx.save();
        ctx.globalAlpha = cloud.opacity;

        // Cloud body - multiple overlapping ellipses
        const drawBlob = (bx: number, by: number, rw: number, rh: number) => {
          ctx.beginPath();
          ctx.ellipse(bx, by, rw, rh, 0, 0, Math.PI * 2);
          ctx.fill();
        };

        ctx.fillStyle = "rgba(255, 250, 240, 0.8)";
        drawBlob(cx, cy, cw * 0.4, ch);
        drawBlob(cx - cw * 0.25, cy + ch * 0.3, cw * 0.3, ch * 0.8);
        drawBlob(cx + cw * 0.2, cy + ch * 0.2, cw * 0.35, ch * 0.7);
        drawBlob(cx + cw * 0.4, cy + ch * 0.4, cw * 0.25, ch * 0.6);

        // Cloud highlight
        ctx.fillStyle = "rgba(255, 240, 200, 0.4)";
        drawBlob(cx - cw * 0.1, cy - ch * 0.2, cw * 0.3, ch * 0.5);

        ctx.restore();
      }
    }

    function drawTempleSilhouette(w: number, h: number) {
      const tx = w * 0.35;
      const ty = h * 0.72;
      const tw = w * 0.04;

      ctx.fillStyle = "rgba(80, 70, 55, 0.55)";

      // Main temple body
      ctx.beginPath();
      ctx.moveTo(tx - tw * 0.5, ty);
      ctx.lineTo(tx - tw * 0.4, ty - tw * 1.2);
      ctx.lineTo(tx - tw * 0.25, ty - tw * 1.5);
      ctx.lineTo(tx - tw * 0.15, ty - tw * 1.8);
      ctx.lineTo(tx - tw * 0.08, ty - tw * 2.0);
      ctx.lineTo(tx, ty - tw * 2.4);
      ctx.lineTo(tx + tw * 0.08, ty - tw * 2.0);
      ctx.lineTo(tx + tw * 0.15, ty - tw * 1.8);
      ctx.lineTo(tx + tw * 0.25, ty - tw * 1.5);
      ctx.lineTo(tx + tw * 0.4, ty - tw * 1.2);
      ctx.lineTo(tx + tw * 0.5, ty);
      ctx.closePath();
      ctx.fill();

      // Temple spire glow
      const spireGlow = ctx.createRadialGradient(
        tx, ty - tw * 2.4, 0,
        tx, ty - tw * 2.4, tw * 0.3
      );
      spireGlow.addColorStop(0, "rgba(212, 160, 48, 0.15)");
      spireGlow.addColorStop(1, "rgba(212, 160, 48, 0)");
      ctx.fillStyle = spireGlow;
      ctx.beginPath();
      ctx.arc(tx, ty - tw * 2.4, tw * 0.3, 0, Math.PI * 2);
      ctx.fill();

      // Pillars
      ctx.fillStyle = "rgba(70, 62, 48, 0.45)";
      for (let i = -2; i <= 2; i++) {
        const px = tx + i * tw * 0.15;
        ctx.fillRect(px - 1, ty - tw * 0.9, 2.5, tw * 0.9);
      }
    }

    function drawChariotSilhouette(w: number, h: number) {
      const cx = w * 0.7;
      const cy = h * 0.7;
      const scale = Math.min(w, h) * 0.0008;

      ctx.save();
      ctx.fillStyle = "rgba(65, 55, 42, 0.45)";
      ctx.translate(cx, cy);
      ctx.scale(scale, scale);

      // Chariot body
      ctx.beginPath();
      ctx.moveTo(-30, 0);
      ctx.lineTo(-25, -25);
      ctx.lineTo(25, -25);
      ctx.lineTo(30, 0);
      ctx.closePath();
      ctx.fill();

      // Chariot wheels
      ctx.beginPath();
      ctx.arc(-20, 5, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(20, 5, 8, 0, Math.PI * 2);
      ctx.fill();

      // Horse silhouette (simplified)
      ctx.beginPath();
      ctx.moveTo(-30, -10);
      ctx.lineTo(-55, -15);
      ctx.lineTo(-60, -35);
      ctx.lineTo(-55, -42);
      ctx.lineTo(-50, -38);
      ctx.lineTo(-48, -30);
      ctx.lineTo(-42, -25);
      ctx.lineTo(-38, -15);
      ctx.closePath();
      ctx.fill();

      // Horse legs
      ctx.fillRect(-58, -15, 2, 15);
      ctx.fillRect(-52, -15, 2, 15);
      ctx.fillRect(-45, -12, 2, 12);
      ctx.fillRect(-40, -10, 2, 10);

      // Figure 1 - Krishna (driver, slightly taller)
      ctx.beginPath();
      ctx.moveTo(-5, -25);
      ctx.lineTo(-8, -55);
      ctx.lineTo(-4, -62);
      ctx.lineTo(0, -55);
      ctx.lineTo(5, -25);
      ctx.closePath();
      ctx.fill();
      // Head
      ctx.beginPath();
      ctx.arc(0, -65, 5, 0, Math.PI * 2);
      ctx.fill();

      // Figure 2 - Arjuna (seated/reclining)
      ctx.beginPath();
      ctx.moveTo(8, -25);
      ctx.lineTo(10, -45);
      ctx.lineTo(16, -50);
      ctx.lineTo(22, -45);
      ctx.lineTo(20, -25);
      ctx.closePath();
      ctx.fill();
      // Head
      ctx.beginPath();
      ctx.arc(18, -52, 4, 0, Math.PI * 2);
      ctx.fill();

      // Chariot flag (dharma flag)
      ctx.beginPath();
      ctx.moveTo(0, -65);
      ctx.lineTo(0, -85);
      ctx.lineTo(15, -80);
      ctx.lineTo(0, -75);
      ctx.closePath();
      ctx.fill();

      ctx.restore();
    }

    function drawShivaPresence(w: number, h: number) {
      // Subtle crescent moon in the upper sky
      const mx = w * 0.2;
      const my = h * 0.12;
      const mr = Math.min(w, h) * 0.02;

      ctx.save();
      ctx.globalAlpha = 0.15 + Math.sin(t * 0.0003) * 0.03;

      // Moon glow
      const moonGlow = ctx.createRadialGradient(mx, my, 0, mx, my, mr * 4);
      moonGlow.addColorStop(0, "rgba(200, 180, 160, 0.3)");
      moonGlow.addColorStop(1, "rgba(200, 180, 160, 0)");
      ctx.fillStyle = moonGlow;
      ctx.beginPath();
      ctx.arc(mx, my, mr * 4, 0, Math.PI * 2);
      ctx.fill();

      // Crescent moon
      ctx.fillStyle = "rgba(220, 210, 195, 0.8)";
      ctx.beginPath();
      ctx.arc(mx, my, mr, 0, Math.PI * 2);
      ctx.fill();
      // Cut out to make crescent
      ctx.globalCompositeOperation = "destination-out";
      ctx.beginPath();
      ctx.arc(mx + mr * 0.4, my - mr * 0.2, mr * 0.85, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalCompositeOperation = "source-over";

      ctx.restore();
    }

    function drawMist(w: number, h: number) {
      const mistY = h * 0.72;
      const grad = ctx.createLinearGradient(0, mistY, 0, h);
      grad.addColorStop(0, "rgba(232, 222, 208, 0)");
      grad.addColorStop(0.3, "rgba(232, 222, 208, 0.15)");
      grad.addColorStop(0.6, "rgba(240, 232, 218, 0.25)");
      grad.addColorStop(1, "rgba(248, 246, 242, 0.6)");
      ctx.fillStyle = grad;
      ctx.fillRect(0, mistY, w, h - mistY);
    }

    function drawParticles(w: number, h: number) {
      if (Math.random() < 0.04) spawnParticle();
      particles = particles.filter((p) => p.opacity > 0.001);

      for (const p of particles) {
        p.x += p.driftX + Math.sin(t * 0.001 + p.phase) * 0.08;
        p.y -= p.driftSpeed;
        p.opacity = Math.min(p.opacity + 0.005, 0.3) * (1 - (p.y / h) * 0.002);

        if (p.y < 0) p.opacity *= 0.5;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        const warmth = Math.sin(t * 0.001 + p.phase) * 0.5 + 0.5;
        ctx.fillStyle = `rgba(${200 + warmth * 55}, ${180 + warmth * 40}, ${140 + warmth * 30}, ${p.opacity})`;
        ctx.fill();
      }
    }

    // ── Main animation loop ──
    const animate = () => {
      t++;
      const w = canvas.width;
      const h = canvas.height;

      ctx.clearRect(0, 0, w, h);

      drawSky(w, h);
      drawSun(w, h);
      drawLightRays(w, h);
      drawShivaPresence(w, h);
      drawClouds(w, h);
      drawMountains(farMountains, w, h);
      drawMountains(midMountains, w, h);
      drawTempleSilhouette(w, h);
      drawChariotSilhouette(w, h);
      drawMountains(nearMountains, w, h);
      drawMist(w, h);
      drawParticles(w, h);

      // Bottom fade to match page background
      const bottomGrad = ctx.createLinearGradient(0, h * 0.85, 0, h);
      bottomGrad.addColorStop(0, "rgba(248, 246, 242, 0)");
      bottomGrad.addColorStop(1, "rgba(248, 246, 242, 0.95)");
      ctx.fillStyle = bottomGrad;
      ctx.fillRect(0, h * 0.85, w, h * 0.15);

      animRef.current = requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => {
      dpr = resize(canvas);
      initMountains();
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
