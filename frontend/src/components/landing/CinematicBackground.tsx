"use client";

import { useEffect, useRef, useCallback } from "react";

interface Cloud {
  x: number;
  y: number;
  width: number;
  height: number;
  speed: number;
  opacity: number;
  drift: number;
}

interface MountainLayer {
  points: { x: number; y: number }[];
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
  life: number;
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
    let w = canvas.width;
    let h = canvas.height;

    // ── Smooth mountain generation using bezier-like interpolation ──
    function genMountainPoints(
      baseY: number,
      numPeaks: number,
      amplitude: number,
      seed: number
    ): { x: number; y: number }[] {
      const points: { x: number; y: number }[] = [];
      const step = w / (numPeaks - 1);
      for (let i = 0; i < numPeaks; i++) {
        const x = i * step;
        const noise =
          Math.sin(i * 1.7 + seed) * 0.4 +
          Math.sin(i * 3.1 + seed * 2) * 0.2 +
          Math.sin(i * 0.5 + seed * 0.7) * 0.4;
        const peakShape = Math.sin((i / (numPeaks - 1)) * Math.PI);
        const y = baseY * h + noise * amplitude * h + peakShape * amplitude * h * 0.3;
        points.push({ x, y });
      }
      return points;
    }

    let farMountains: MountainLayer = {
      points: [],
      color: "rgba(150, 140, 128, 0.20)",
      parallax: 0.002,
    };
    let midMountains: MountainLayer = {
      points: [],
      color: "rgba(110, 100, 88, 0.30)",
      parallax: 0.005,
    };
    let nearMountains: MountainLayer = {
      points: [],
      color: "rgba(75, 68, 58, 0.42)",
      parallax: 0.009,
    };

    function initMountains() {
      if (!canvas) return;
      w = canvas.width;
      h = canvas.height;
      farMountains.points = genMountainPoints(0.60, 14, 0.04, 42);
      midMountains.points = genMountainPoints(0.66, 12, 0.05, 17);
      nearMountains.points = genMountainPoints(0.73, 10, 0.04, 73);
    }
    initMountains();

    // ── Clouds ──
    const clouds: Cloud[] = [];
    for (let i = 0; i < 7; i++) {
      clouds.push({
        x: Math.random() * 2.5 - 0.75,
        y: 0.10 + Math.random() * 0.22,
        width: 0.10 + Math.random() * 0.18,
        height: 0.015 + Math.random() * 0.02,
        speed: 0.00002 + Math.random() * 0.00003,
        opacity: 0.08 + Math.random() * 0.12,
        drift: Math.sin(Math.random() * 10) * 0.00001,
      });
    }

    // ── Particles ──
    let particles: Particle[] = [];
    function spawnParticle() {
      particles.push({
        x: Math.random() * w,
        y: h * 0.35 + Math.random() * h * 0.5,
        size: 0.8 + Math.random() * 1.8,
        opacity: 0,
        driftX: (Math.random() - 0.5) * 0.12,
        driftSpeed: 0.05 + Math.random() * 0.10,
        phase: Math.random() * Math.PI * 2,
        life: 0,
      });
    }

    // ── Draw: Sky ──
    function drawSky() {
      const grad = ctx.createLinearGradient(0, 0, 0, h);
      grad.addColorStop(0, "#c0b8ae");
      grad.addColorStop(0.15, "#d0c8bc");
      grad.addColorStop(0.30, "#ddd5c8");
      grad.addColorStop(0.50, "#e8dece");
      grad.addColorStop(0.65, "#f0e4cc");
      grad.addColorStop(0.78, "#ecd4a8");
      grad.addColorStop(0.90, "#e0c080");
      grad.addColorStop(1.0, "#d0a858");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);
    }

    // ── Draw: Sun with glow ──
    function drawSun() {
      const sx = w * 0.60;
      const sy = h * 0.55;
      const sr = Math.min(w, h) * 0.055;

      // Outer atmospheric glow
      const glow = ctx.createRadialGradient(sx, sy, 0, sx, sy, sr * 6);
      glow.addColorStop(0, "rgba(255, 215, 130, 0.22)");
      glow.addColorStop(0.3, "rgba(255, 205, 110, 0.10)");
      glow.addColorStop(0.7, "rgba(255, 190, 90, 0.03)");
      glow.addColorStop(1, "rgba(255, 180, 80, 0)");
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, w, h);

      // Sun disc
      const sg = ctx.createRadialGradient(sx, sy, 0, sx, sy, sr);
      sg.addColorStop(0, "rgba(255, 225, 155, 0.85)");
      sg.addColorStop(0.5, "rgba(255, 210, 130, 0.55)");
      sg.addColorStop(0.8, "rgba(255, 195, 105, 0.20)");
      sg.addColorStop(1, "rgba(255, 180, 80, 0)");
      ctx.fillStyle = sg;
      ctx.beginPath();
      ctx.arc(sx, sy, sr, 0, Math.PI * 2);
      ctx.fill();
    }

    // ── Draw: Light rays ──
    function drawLightRays() {
      const sx = w * 0.60;
      const sy = h * 0.55;
      ctx.save();
      ctx.globalAlpha = 0.035 + Math.sin(t * 0.0004) * 0.01;
      for (let i = 0; i < 12; i++) {
        const angle = (i / 12) * Math.PI * 0.7 - 0.15;
        const rayLen = h * 0.9;
        const rayWidth = w * 0.02 + Math.sin(i * 2.1 + t * 0.0003) * w * 0.005;
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(
          sx + Math.cos(angle - 0.015) * rayLen,
          sy + Math.sin(angle - 0.015) * rayLen
        );
        ctx.lineTo(
          sx + Math.cos(angle + 0.015) * rayLen,
          sy + Math.sin(angle + 0.015) * rayLen
        );
        ctx.closePath();
        const rayGrad = ctx.createLinearGradient(
          sx, sy,
          sx + Math.cos(angle) * rayLen,
          sy + Math.sin(angle) * rayLen
        );
        rayGrad.addColorStop(0, "rgba(255, 215, 140, 0.5)");
        rayGrad.addColorStop(0.3, "rgba(255, 200, 120, 0.2)");
        rayGrad.addColorStop(1, "rgba(255, 190, 100, 0)");
        ctx.fillStyle = rayGrad;
        ctx.fill();
      }
      ctx.restore();
    }

    // ── Draw: Clouds ──
    function drawClouds() {
      for (const c of clouds) {
        c.x += c.speed + c.drift;
        if (c.x > 2) c.x = -c.width - 0.2;

        const cx = c.x * w;
        const cy = c.y * h;
        const cw = c.width * w;
        const ch = c.height * h;

        ctx.save();
        ctx.globalAlpha = c.opacity + Math.sin(t * 0.0002 + c.x * 5) * 0.02;
        const cg = ctx.createRadialGradient(cx, cy, 0, cx, cy, cw * 0.5);
        cg.addColorStop(0, "rgba(240, 235, 225, 0.8)");
        cg.addColorStop(0.5, "rgba(235, 228, 215, 0.4)");
        cg.addColorStop(1, "rgba(230, 222, 208, 0)");
        ctx.fillStyle = cg;
        ctx.beginPath();
        ctx.ellipse(cx, cy, cw * 0.5, ch, 0, 0, Math.PI * 2);
        ctx.fill();
        // Secondary lobe for organic shape
        ctx.beginPath();
        ctx.ellipse(cx + cw * 0.2, cy - ch * 0.3, cw * 0.3, ch * 0.7, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }

    // ── Draw: Smooth mountains ──
    function drawMountain(layer: MountainLayer) {
      const pts = layer.points;
      const offset = Math.sin(t * 0.0002) * layer.parallax * w * 0.3;

      ctx.save();
      ctx.fillStyle = layer.color;
      ctx.beginPath();
      ctx.moveTo(-10 + offset, h + 10);

      // Draw smooth curve through points
      ctx.moveTo(pts[0].x + offset, pts[0].y);
      for (let i = 1; i < pts.length; i++) {
        const prev = pts[i - 1];
        const curr = pts[i];
        const cpx = (prev.x + curr.x) / 2 + offset;
        ctx.quadraticCurveTo(prev.x + offset, prev.y, cpx, (prev.y + curr.y) / 2);
      }
      ctx.lineTo(pts[pts.length - 1].x + offset, pts[pts.length - 1].y);
      ctx.lineTo(w + 10, h + 10);
      ctx.lineTo(-10, h + 10);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }

    // ── Draw: Temple silhouette ──
    function drawTemple() {
      const tx = w * 0.45;
      const baseY = h * 0.70;
      const scale = Math.min(w, h) * 0.0008;

      ctx.save();
      ctx.fillStyle = "rgba(60, 52, 42, 0.50)";

      // Main tower (shikhara)
      ctx.beginPath();
      ctx.moveTo(tx - 18 * scale, baseY);
      ctx.lineTo(tx - 12 * scale, baseY - 60 * scale);
      ctx.lineTo(tx - 8 * scale, baseY - 90 * scale);
      ctx.lineTo(tx - 4 * scale, baseY - 110 * scale);
      ctx.lineTo(tx, baseY - 125 * scale);
      ctx.lineTo(tx + 4 * scale, baseY - 110 * scale);
      ctx.lineTo(tx + 8 * scale, baseY - 90 * scale);
      ctx.lineTo(tx + 12 * scale, baseY - 60 * scale);
      ctx.lineTo(tx + 18 * scale, baseY);
      ctx.closePath();
      ctx.fill();

      // Mandapa (base platform)
      ctx.fillRect(tx - 30 * scale, baseY, 60 * scale, 8 * scale);

      // Side pillars
      ctx.fillRect(tx - 22 * scale, baseY - 30 * scale, 3 * scale, 30 * scale);
      ctx.fillRect(tx + 19 * scale, baseY - 30 * scale, 3 * scale, 30 * scale);

      // Kalasha (spire top)
      ctx.beginPath();
      ctx.arc(tx, baseY - 128 * scale, 3 * scale, 0, Math.PI * 2);
      ctx.fill();

      // Gold glow on spire
      ctx.globalAlpha = 0.25 + Math.sin(t * 0.0006) * 0.08;
      const sg = ctx.createRadialGradient(
        tx, baseY - 115 * scale, 0,
        tx, baseY - 115 * scale, 25 * scale
      );
      sg.addColorStop(0, "rgba(212, 160, 48, 0.4)");
      sg.addColorStop(1, "rgba(212, 160, 48, 0)");
      ctx.fillStyle = sg;
      ctx.beginPath();
      ctx.arc(tx, baseY - 115 * scale, 25 * scale, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }

    // ── Draw: Chariot silhouette (Krishna & Arjuna) ──
    function drawChariot() {
      const cx = w * 0.72;
      const cy = h * 0.73;
      const s = Math.min(w, h) * 0.0006;

      ctx.save();
      ctx.fillStyle = "rgba(55, 48, 38, 0.45)";

      // Chariot body
      ctx.beginPath();
      ctx.moveTo(cx - 10 * s, cy);
      ctx.lineTo(cx + 30 * s, cy);
      ctx.lineTo(cx + 32 * s, cy - 12 * s);
      ctx.lineTo(cx - 8 * s, cy - 12 * s);
      ctx.closePath();
      ctx.fill();

      // Wheels
      ctx.beginPath();
      ctx.arc(cx - 2 * s, cy + 3 * s, 4 * s, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx + 22 * s, cy + 3 * s, 4 * s, 0, Math.PI * 2);
      ctx.fill();

      // Horse body
      ctx.beginPath();
      ctx.moveTo(cx - 10 * s, cy - 8 * s);
      ctx.bezierCurveTo(cx - 30 * s, cy - 14 * s, cx - 40 * s, cy - 20 * s, cx - 48 * s, cy - 16 * s);
      ctx.bezierCurveTo(cx - 52 * s, cy - 14 * s, cx - 54 * s, cy - 8 * s, cx - 50 * s, cy - 2 * s);
      ctx.lineTo(cx - 10 * s, cy - 2 * s);
      ctx.closePath();
      ctx.fill();

      // Horse neck and head
      ctx.beginPath();
      ctx.moveTo(cx - 42 * s, cy - 16 * s);
      ctx.bezierCurveTo(cx - 48 * s, cy - 32 * s, cx - 52 * s, cy - 36 * s, cx - 56 * s, cy - 32 * s);
      ctx.bezierCurveTo(cx - 58 * s, cy - 30 * s, cx - 56 * s, cy - 26 * s, cx - 50 * s, cy - 22 * s);
      ctx.lineTo(cx - 42 * s, cy - 16 * s);
      ctx.closePath();
      ctx.fill();

      // Horse legs
      ctx.fillRect(cx - 46 * s, cy - 2 * s, 1.5 * s, 8 * s);
      ctx.fillRect(cx - 38 * s, cy - 2 * s, 1.5 * s, 7 * s);
      ctx.fillRect(cx - 20 * s, cy - 2 * s, 1.5 * s, 8 * s);
      ctx.fillRect(cx - 12 * s, cy - 2 * s, 1.5 * s, 7 * s);

      // Krishna (charioteer, taller)
      ctx.beginPath();
      ctx.moveTo(cx + 2 * s, cy - 12 * s);
      ctx.lineTo(cx + 1 * s, cy - 40 * s);
      ctx.bezierCurveTo(cx + 1 * s, cy - 44 * s, cx + 3 * s, cy - 48 * s, cx + 5 * s, cy - 48 * s);
      ctx.bezierCurveTo(cx + 7 * s, cy - 48 * s, cx + 9 * s, cy - 44 * s, cx + 9 * s, cy - 40 * s);
      ctx.lineTo(cx + 8 * s, cy - 12 * s);
      ctx.closePath();
      ctx.fill();
      // Krishna head
      ctx.beginPath();
      ctx.arc(cx + 5 * s, cy - 51 * s, 4 * s, 0, Math.PI * 2);
      ctx.fill();
      // Crown peak
      ctx.beginPath();
      ctx.moveTo(cx + 2 * s, cy - 53 * s);
      ctx.lineTo(cx + 5 * s, cy - 58 * s);
      ctx.lineTo(cx + 8 * s, cy - 53 * s);
      ctx.closePath();
      ctx.fill();

      // Arjuna (seated)
      ctx.beginPath();
      ctx.moveTo(cx + 14 * s, cy - 12 * s);
      ctx.lineTo(cx + 15 * s, cy - 30 * s);
      ctx.bezierCurveTo(cx + 15 * s, cy - 34 * s, cx + 17 * s, cy - 36 * s, cx + 19 * s, cy - 36 * s);
      ctx.bezierCurveTo(cx + 21 * s, cy - 36 * s, cx + 23 * s, cy - 34 * s, cx + 23 * s, cy - 30 * s);
      ctx.lineTo(cx + 24 * s, cy - 12 * s);
      ctx.closePath();
      ctx.fill();
      // Arjuna head
      ctx.beginPath();
      ctx.arc(cx + 19 * s, cy - 38 * s, 3.5 * s, 0, Math.PI * 2);
      ctx.fill();

      // Dharma flag
      ctx.strokeStyle = "rgba(55, 48, 38, 0.45)";
      ctx.lineWidth = 1.5 * s;
      ctx.beginPath();
      ctx.moveTo(cx + 5 * s, cy - 58 * s);
      ctx.lineTo(cx + 5 * s, cy - 75 * s);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(cx + 5 * s, cy - 75 * s);
      ctx.lineTo(cx + 18 * s, cy - 70 * s);
      ctx.lineTo(cx + 5 * s, cy - 65 * s);
      ctx.closePath();
      ctx.fill();

      ctx.restore();
    }

    // ── Draw: Shiva presence (crescent moon) ──
    function drawShivaPresence() {
      const mx = w * 0.18;
      const my = h * 0.10;
      const mr = Math.min(w, h) * 0.018;

      ctx.save();
      ctx.globalAlpha = 0.14 + Math.sin(t * 0.0003) * 0.03;

      // Moon glow
      const mg = ctx.createRadialGradient(mx, my, 0, mx, my, mr * 5);
      mg.addColorStop(0, "rgba(210, 200, 185, 0.25)");
      mg.addColorStop(0.5, "rgba(200, 190, 175, 0.08)");
      mg.addColorStop(1, "rgba(200, 190, 175, 0)");
      ctx.fillStyle = mg;
      ctx.beginPath();
      ctx.arc(mx, my, mr * 5, 0, Math.PI * 2);
      ctx.fill();

      // Crescent moon
      ctx.fillStyle = "rgba(225, 218, 205, 0.8)";
      ctx.beginPath();
      ctx.arc(mx, my, mr, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalCompositeOperation = "destination-out";
      ctx.beginPath();
      ctx.arc(mx + mr * 0.4, my - mr * 0.15, mr * 0.82, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalCompositeOperation = "source-over";

      ctx.restore();
    }

    // ── Draw: Valley mist ──
    function drawMist() {
      const mistY = h * 0.70;
      const grad = ctx.createLinearGradient(0, mistY, 0, h);
      grad.addColorStop(0, "rgba(232, 224, 210, 0)");
      grad.addColorStop(0.2, "rgba(235, 228, 215, 0.08)");
      grad.addColorStop(0.5, "rgba(240, 234, 220, 0.18)");
      grad.addColorStop(0.8, "rgba(245, 240, 230, 0.35)");
      grad.addColorStop(1, "rgba(248, 246, 242, 0.65)");
      ctx.fillStyle = grad;
      ctx.fillRect(0, mistY, w, h - mistY);
    }

    // ── Draw: Floating particles ──
    function drawParticles() {
      if (Math.random() < 0.02) spawnParticle();
      particles = particles.filter((p) => p.life < 300);

      for (const p of particles) {
        p.x += p.driftX + Math.sin(t * 0.0008 + p.phase) * 0.06;
        p.y -= p.driftSpeed;
        p.life++;

        // Fade in and out
        if (p.life < 50) p.opacity = p.life / 50 * 0.18;
        else if (p.life > 240) p.opacity = Math.max(0, (300 - p.life) / 60 * 0.18);
        else p.opacity = 0.18;

        if (p.y < 0) p.opacity *= 0.3;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        const warmth = Math.sin(t * 0.0008 + p.phase) * 0.5 + 0.5;
        ctx.fillStyle = `rgba(${210 + warmth * 40}, ${190 + warmth * 30}, ${150 + warmth * 20}, ${p.opacity})`;
        ctx.fill();
      }
    }

    // ── Main animation loop ──
    const animate = () => {
      t++;
      w = canvas.width;
      h = canvas.height;

      ctx.clearRect(0, 0, w, h);

      drawSky();
      drawSun();
      drawLightRays();
      drawShivaPresence();
      drawClouds();
      drawMountain(farMountains);
      drawMountain(midMountains);
      drawTemple();
      drawChariot();
      drawMountain(nearMountains);
      drawMist();
      drawParticles();

      // Bottom fade to page background
      const bGrad = ctx.createLinearGradient(0, h * 0.78, 0, h);
      bGrad.addColorStop(0, "rgba(248, 246, 242, 0)");
      bGrad.addColorStop(0.4, "rgba(248, 246, 242, 0.25)");
      bGrad.addColorStop(0.8, "rgba(248, 246, 242, 0.75)");
      bGrad.addColorStop(1, "rgba(248, 246, 242, 0.97)");
      ctx.fillStyle = bGrad;
      ctx.fillRect(0, h * 0.82, w, h * 0.18);

      animRef.current = requestAnimationFrame(animate);
    };
    animate();

    const handleResize = () => {
      dpr = resize(canvas);
      w = canvas.width;
      h = canvas.height;
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
