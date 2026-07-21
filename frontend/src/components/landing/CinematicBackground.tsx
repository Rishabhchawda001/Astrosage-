"use client";

import { useEffect, useRef, useCallback } from "react";

/* ════════════════════════════════════════════════════════════════
   AstroSage AI — Cinematic Background
   Dawn on Kurukshetra: Krishna, Arjuna, and the presence of Shiva
   ════════════════════════════════════════════════════════════════ */

interface Cloud {
  x: number;
  y: number;
  w: number;
  h: number;
  speed: number;
  opacity: number;
  lobes: number;
}

interface MountainLayer {
  points: { x: number; y: number }[];
  color: string;
  parallax: number;
}

interface Dust {
  x: number;
  y: number;
  size: number;
  opacity: number;
  vx: number;
  vy: number;
  phase: number;
  life: number;
  maxLife: number;
}

export function CinematicBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);

  const setupCanvas = useCallback((canvas: HTMLCanvasElement) => {
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
    let dpr = setupCanvas(canvas);
    const ctx = canvas.getContext("2d")!;
    let t = 0;
    let W = canvas.width;
    let H = canvas.height;

    /* ── Mountain generation ── */
    function genPeaks(
      baseY: number,
      count: number,
      amp: number,
      seed: number
    ): { x: number; y: number }[] {
      const pts: { x: number; y: number }[] = [];
      const step = W / (count - 1);
      for (let i = 0; i < count; i++) {
        const x = i * step;
        const n =
          Math.sin(i * 1.7 + seed) * 0.35 +
          Math.sin(i * 3.1 + seed * 2) * 0.2 +
          Math.sin(i * 0.5 + seed * 0.7) * 0.35 +
          Math.cos(i * 2.3 + seed * 1.3) * 0.1;
        const bell = Math.sin((i / (count - 1)) * Math.PI);
        const y = baseY * H + n * amp * H + bell * amp * H * 0.25;
        pts.push({ x, y });
      }
      return pts;
    }

    let farMtn: MountainLayer = {
      points: [],
      color: "rgba(145, 138, 125, 0.18)",
      parallax: 0.0015,
    };
    let midMtn: MountainLayer = {
      points: [],
      color: "rgba(105, 95, 82, 0.28)",
      parallax: 0.004,
    };
    let nearMtn: MountainLayer = {
      points: [],
      color: "rgba(70, 62, 52, 0.40)",
      parallax: 0.008,
    };

    function initTerrain() {
      if (!canvas) return;
      W = canvas.width;
      H = canvas.height;
      farMtn.points = genPeaks(0.58, 16, 0.045, 42);
      midMtn.points = genPeaks(0.65, 14, 0.055, 17);
      nearMtn.points = genPeaks(0.74, 12, 0.04, 73);
    }
    initTerrain();

    /* ── Clouds ── */
    const clouds: Cloud[] = [];
    for (let i = 0; i < 8; i++) {
      clouds.push({
        x: Math.random() * 2.5 - 0.75,
        y: 0.06 + Math.random() * 0.25,
        w: 0.08 + Math.random() * 0.16,
        h: 0.012 + Math.random() * 0.018,
        speed: 0.000015 + Math.random() * 0.000025,
        opacity: 0.06 + Math.random() * 0.10,
        lobes: 2 + Math.floor(Math.random() * 2),
      });
    }

    /* ── Dust particles ── */
    let dust: Dust[] = [];
    function spawnDust() {
      dust.push({
        x: Math.random() * W,
        y: H * 0.30 + Math.random() * H * 0.55,
        size: 0.6 + Math.random() * 1.6,
        opacity: 0,
        vx: (Math.random() - 0.5) * 0.10,
        vy: -(0.03 + Math.random() * 0.08),
        phase: Math.random() * Math.PI * 2,
        life: 0,
        maxLife: 200 + Math.random() * 200,
      });
    }

    /* ════════════════════════════════════════════════════════════
       DRAW FUNCTIONS
       ════════════════════════════════════════════════════════════ */

    /* ── Sky ── */
    function drawSky() {
      const g = ctx.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0.0, "#b8b2a8");
      g.addColorStop(0.10, "#c8c0b5");
      g.addColorStop(0.22, "#d5cdc2");
      g.addColorStop(0.38, "#e2dace");
      g.addColorStop(0.52, "#ece2d0");
      g.addColorStop(0.65, "#f0e4cc");
      g.addColorStop(0.76, "#ecd2a5");
      g.addColorStop(0.88, "#e0c078");
      g.addColorStop(1.0, "#d0a850");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
    }

    /* ── Sun ── */
    function drawSun() {
      const sx = W * 0.58;
      const sy = H * 0.54;
      const sr = Math.min(W, H) * 0.052;

      // Atmospheric glow
      const glow = ctx.createRadialGradient(sx, sy, 0, sx, sy, sr * 7);
      glow.addColorStop(0, "rgba(255, 218, 140, 0.20)");
      glow.addColorStop(0.25, "rgba(255, 210, 120, 0.10)");
      glow.addColorStop(0.55, "rgba(255, 200, 100, 0.04)");
      glow.addColorStop(1, "rgba(255, 190, 80, 0)");
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, W, H);

      // Disc
      const sg = ctx.createRadialGradient(sx, sy, 0, sx, sy, sr);
      sg.addColorStop(0, "rgba(255, 228, 160, 0.82)");
      sg.addColorStop(0.45, "rgba(255, 215, 140, 0.50)");
      sg.addColorStop(0.75, "rgba(255, 200, 115, 0.18)");
      sg.addColorStop(1, "rgba(255, 185, 90, 0)");
      ctx.fillStyle = sg;
      ctx.beginPath();
      ctx.arc(sx, sy, sr, 0, Math.PI * 2);
      ctx.fill();
    }

    /* ── Volumetric light rays ── */
    function drawRays() {
      const sx = W * 0.58;
      const sy = H * 0.54;
      ctx.save();
      ctx.globalAlpha = 0.030 + Math.sin(t * 0.00035) * 0.008;
      for (let i = 0; i < 14; i++) {
        const a = (i / 14) * Math.PI * 0.65 - 0.12;
        const len = H * 0.85;
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(sx + Math.cos(a - 0.012) * len, sy + Math.sin(a - 0.012) * len);
        ctx.lineTo(sx + Math.cos(a + 0.012) * len, sy + Math.sin(a + 0.012) * len);
        ctx.closePath();
        const rg = ctx.createLinearGradient(
          sx, sy,
          sx + Math.cos(a) * len, sy + Math.sin(a) * len
        );
        rg.addColorStop(0, "rgba(255, 220, 150, 0.45)");
        rg.addColorStop(0.25, "rgba(255, 210, 130, 0.18)");
        rg.addColorStop(1, "rgba(255, 200, 110, 0)");
        ctx.fillStyle = rg;
        ctx.fill();
      }
      ctx.restore();
    }

    /* ── Clouds ── */
    function drawClouds() {
      for (const c of clouds) {
        c.x += c.speed;
        if (c.x > 2.2) c.x = -c.w - 0.3;

        const cx = c.x * W;
        const cy = c.y * H;
        const cw = c.w * W;
        const ch = c.h * H;

        ctx.save();
        ctx.globalAlpha = c.opacity + Math.sin(t * 0.00015 + c.x * 8) * 0.015;
        const cg = ctx.createRadialGradient(cx, cy, 0, cx, cy, cw * 0.5);
        cg.addColorStop(0, "rgba(238, 232, 222, 0.75)");
        cg.addColorStop(0.5, "rgba(235, 228, 215, 0.35)");
        cg.addColorStop(1, "rgba(230, 222, 208, 0)");
        ctx.fillStyle = cg;

        for (let l = 0; l < c.lobes; l++) {
          const lx = cx + (l - (c.lobes - 1) / 2) * cw * 0.22;
          const ly = cy - ch * 0.15 * Math.sin(l * 1.8);
          ctx.beginPath();
          ctx.ellipse(lx, ly, cw * (0.35 - l * 0.02), ch * (0.8 - l * 0.05), 0, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }
    }

    /* ── Mountain layers ── */
    function drawMtn(layer: MountainLayer) {
      const pts = layer.points;
      const off = Math.sin(t * 0.00015) * layer.parallax * W * 0.25;
      ctx.save();
      ctx.fillStyle = layer.color;
      ctx.beginPath();
      ctx.moveTo(pts[0].x + off, pts[0].y);
      for (let i = 1; i < pts.length; i++) {
        const p = pts[i - 1];
        const c = pts[i];
        const mx = (p.x + c.x) / 2 + off;
        const my = (p.y + c.y) / 2;
        ctx.quadraticCurveTo(p.x + off, p.y, mx, my);
      }
      ctx.lineTo(pts[pts.length - 1].x + off, pts[pts.length - 1].y);
      ctx.lineTo(W + 10, H + 10);
      ctx.lineTo(-10, H + 10);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }

    /* ── Shiva: meditation figure on distant Himalayan peak ──
       A majestic silhouette emerging from the far mountain ridge.
       Seated in padmasana, trident beside him, subtle divine glow. */
    function drawShiva() {
      const px = W * 0.14;
      const py = H * 0.52;
      const s = Math.min(W, H) * 0.00045;

      ctx.save();
      ctx.fillStyle = "rgba(120, 112, 98, 0.22)";

      // Seated body (broad base tapering up)
      ctx.beginPath();
      ctx.moveTo(px - 18 * s, py + 2 * s);
      ctx.bezierCurveTo(px - 20 * s, py - 8 * s, px - 16 * s, py - 22 * s, px - 8 * s, py - 32 * s);
      ctx.bezierCurveTo(px - 4 * s, py - 38 * s, px - 2 * s, py - 42 * s, px, py - 44 * s);
      ctx.bezierCurveTo(px + 2 * s, py - 42 * s, px + 4 * s, py - 38 * s, px + 8 * s, py - 32 * s);
      ctx.bezierCurveTo(px + 16 * s, py - 22 * s, px + 20 * s, py - 8 * s, px + 18 * s, py + 2 * s);
      ctx.closePath();
      ctx.fill();

      // Head
      ctx.beginPath();
      ctx.arc(px, py - 48 * s, 5 * s, 0, Math.PI * 2);
      ctx.fill();

      // Hair knot (jata)
      ctx.beginPath();
      ctx.moveTo(px - 3 * s, py - 52 * s);
      ctx.bezierCurveTo(px - 2 * s, py - 60 * s, px + 2 * s, py - 62 * s, px + 3 * s, py - 56 * s);
      ctx.lineTo(px + 3 * s, py - 52 * s);
      ctx.closePath();
      ctx.fill();

      // Trident (trishula) to the right
      ctx.strokeStyle = "rgba(120, 112, 98, 0.20)";
      ctx.lineWidth = 1.2 * s;
      ctx.beginPath();
      ctx.moveTo(px + 22 * s, py + 5 * s);
      ctx.lineTo(px + 22 * s, py - 60 * s);
      ctx.stroke();
      // Trident prongs
      ctx.beginPath();
      ctx.moveTo(px + 18 * s, py - 60 * s);
      ctx.lineTo(px + 22 * s, py - 68 * s);
      ctx.lineTo(px + 26 * s, py - 60 * s);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(px + 22 * s, py - 56 * s);
      ctx.lineTo(px + 22 * s, py - 66 * s);
      ctx.stroke();

      // Subtle divine glow behind head
      ctx.globalAlpha = 0.06 + Math.sin(t * 0.00025) * 0.02;
      const sg = ctx.createRadialGradient(px, py - 48 * s, 0, px, py - 48 * s, 30 * s);
      sg.addColorStop(0, "rgba(200, 195, 180, 0.4)");
      sg.addColorStop(0.5, "rgba(200, 195, 180, 0.12)");
      sg.addColorStop(1, "rgba(200, 195, 180, 0)");
      ctx.fillStyle = sg;
      ctx.beginPath();
      ctx.arc(px, py - 48 * s, 30 * s, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }

    /* ── Temple silhouette ── */
    function drawTemple() {
      const tx = W * 0.42;
      const by = H * 0.68;
      const s = Math.min(W, H) * 0.0007;

      ctx.save();
      ctx.fillStyle = "rgba(58, 50, 40, 0.48)";

      // Shikhara (tower)
      ctx.beginPath();
      ctx.moveTo(tx - 16 * s, by);
      ctx.lineTo(tx - 10 * s, by - 55 * s);
      ctx.lineTo(tx - 6 * s, by - 82 * s);
      ctx.lineTo(tx - 3 * s, by - 100 * s);
      ctx.lineTo(tx, by - 112 * s);
      ctx.lineTo(tx + 3 * s, by - 100 * s);
      ctx.lineTo(tx + 6 * s, by - 82 * s);
      ctx.lineTo(tx + 10 * s, by - 55 * s);
      ctx.lineTo(tx + 16 * s, by);
      ctx.closePath();
      ctx.fill();

      // Platform
      ctx.fillRect(tx - 26 * s, by, 52 * s, 6 * s);

      // Pillars
      ctx.fillRect(tx - 20 * s, by - 28 * s, 2.5 * s, 28 * s);
      ctx.fillRect(tx + 17.5 * s, by - 28 * s, 2.5 * s, 28 * s);

      // Kalasha (finial)
      ctx.beginPath();
      ctx.arc(tx, by - 115 * s, 2.5 * s, 0, Math.PI * 2);
      ctx.fill();

      // Spire glow
      ctx.globalAlpha = 0.20 + Math.sin(t * 0.0005) * 0.06;
      const sg = ctx.createRadialGradient(tx, by - 100 * s, 0, tx, by - 100 * s, 22 * s);
      sg.addColorStop(0, "rgba(212, 160, 48, 0.35)");
      sg.addColorStop(1, "rgba(212, 160, 48, 0)");
      ctx.fillStyle = sg;
      ctx.beginPath();
      ctx.arc(tx, by - 100 * s, 22 * s, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }

    /* ── Krishna's Chariot ──
       Four white horses, golden chariot, Krishna driving,
       Arjuna seated, dharma flag. */
    function drawChariot() {
      const cx = W * 0.72;
      const cy = H * 0.72;
      const s = Math.min(W, H) * 0.00055;

      ctx.save();

      /* ── Four horses ── */
      ctx.fillStyle = "rgba(210, 205, 195, 0.50)";
      for (let i = 0; i < 4; i++) {
        const hx = cx - 14 * s - i * 10 * s;
        const hy = cy - 6 * s;

        // Body
        ctx.beginPath();
        ctx.moveTo(hx, hy);
        ctx.bezierCurveTo(hx - 8 * s, hy - 10 * s, hx - 20 * s, hy - 14 * s, hx - 28 * s, hy - 10 * s);
        ctx.bezierCurveTo(hx - 30 * s, hy - 8 * s, hx - 30 * s, hy - 2 * s, hx - 26 * s, hy + 2 * s);
        ctx.lineTo(hx + 2 * s, hy + 2 * s);
        ctx.closePath();
        ctx.fill();

        // Neck and head
        ctx.beginPath();
        ctx.moveTo(hx - 24 * s, hy - 10 * s);
        ctx.bezierCurveTo(hx - 30 * s, hy - 22 * s, hx - 34 * s, hy - 26 * s, hx - 36 * s, hy - 22 * s);
        ctx.bezierCurveTo(hx - 37 * s, hy - 20 * s, hx - 35 * s, hy - 16 * s, hx - 30 * s, hy - 14 * s);
        ctx.closePath();
        ctx.fill();

        // Legs
        ctx.fillRect(hx - 26 * s, hy + 2 * s, 1.2 * s, 6 * s);
        ctx.fillRect(hx - 18 * s, hy + 2 * s, 1.2 * s, 5.5 * s);
        ctx.fillRect(hx - 6 * s, hy + 2 * s, 1.2 * s, 6 * s);
        ctx.fillRect(hx + 0 * s, hy + 2 * s, 1.2 * s, 5.5 * s);
      }

      /* ── Chariot body ── */
      ctx.fillStyle = "rgba(65, 55, 42, 0.50)";
      ctx.beginPath();
      ctx.moveTo(cx - 8 * s, cy);
      ctx.lineTo(cx + 32 * s, cy);
      ctx.lineTo(cx + 34 * s, cy - 14 * s);
      ctx.lineTo(cx - 6 * s, cy - 14 * s);
      ctx.closePath();
      ctx.fill();

      // Chariot decorative rail
      ctx.strokeStyle = "rgba(80, 68, 50, 0.35)";
      ctx.lineWidth = 1 * s;
      ctx.beginPath();
      ctx.moveTo(cx - 6 * s, cy - 14 * s);
      ctx.lineTo(cx + 34 * s, cy - 14 * s);
      ctx.stroke();

      // Wheels
      ctx.fillStyle = "rgba(65, 55, 42, 0.45)";
      ctx.beginPath();
      ctx.arc(cx, cy + 4 * s, 4.5 * s, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx + 24 * s, cy + 4 * s, 4.5 * s, 0, Math.PI * 2);
      ctx.fill();

      /* ── Krishna (charioteer, tallest figure) ── */
      ctx.fillStyle = "rgba(55, 48, 38, 0.52)";

      // Body — standing tall
      ctx.beginPath();
      ctx.moveTo(cx + 2 * s, cy - 14 * s);
      ctx.lineTo(cx + 1 * s, cy - 44 * s);
      ctx.bezierCurveTo(cx + 1 * s, cy - 48 * s, cx + 3 * s, cy - 52 * s, cx + 5 * s, cy - 52 * s);
      ctx.bezierCurveTo(cx + 7 * s, cy - 52 * s, cx + 9 * s, cy - 48 * s, cx + 9 * s, cy - 44 * s);
      ctx.lineTo(cx + 8 * s, cy - 14 * s);
      ctx.closePath();
      ctx.fill();

      // Head
      ctx.beginPath();
      ctx.arc(cx + 5 * s, cy - 55 * s, 4.5 * s, 0, Math.PI * 2);
      ctx.fill();

      // Crown (mukuta) — tall conical crown
      ctx.beginPath();
      ctx.moveTo(cx + 1 * s, cy - 58 * s);
      ctx.lineTo(cx + 5 * s, cy - 66 * s);
      ctx.lineTo(cx + 9 * s, cy - 58 * s);
      ctx.closePath();
      ctx.fill();

      // Peacock feather hint (tiny arc above crown)
      ctx.strokeStyle = "rgba(55, 48, 38, 0.35)";
      ctx.lineWidth = 0.8 * s;
      ctx.beginPath();
      ctx.arc(cx + 5 * s, cy - 68 * s, 2 * s, -0.5, Math.PI + 0.5);
      ctx.stroke();

      /* ── Arjuna (seated, respectful posture) ── */
      ctx.fillStyle = "rgba(55, 48, 38, 0.48)";

      // Body — seated
      ctx.beginPath();
      ctx.moveTo(cx + 14 * s, cy - 14 * s);
      ctx.lineTo(cx + 15 * s, cy - 32 * s);
      ctx.bezierCurveTo(cx + 15 * s, cy - 36 * s, cx + 17 * s, cy - 38 * s, cx + 19 * s, cy - 38 * s);
      ctx.bezierCurveTo(cx + 21 * s, cy - 38 * s, cx + 23 * s, cy - 36 * s, cx + 23 * s, cy - 32 * s);
      ctx.lineTo(cx + 24 * s, cy - 14 * s);
      ctx.closePath();
      ctx.fill();

      // Head
      ctx.beginPath();
      ctx.arc(cx + 19 * s, cy - 40 * s, 3.8 * s, 0, Math.PI * 2);
      ctx.fill();

      /* ── Dharma flag ── */
      const flagWave = Math.sin(t * 0.002) * 2 * s;
      ctx.fillStyle = "rgba(55, 48, 38, 0.40)";
      // Pole
      ctx.strokeStyle = "rgba(55, 48, 38, 0.42)";
      ctx.lineWidth = 1.2 * s;
      ctx.beginPath();
      ctx.moveTo(cx + 5 * s, cy - 66 * s);
      ctx.lineTo(cx + 5 * s, cy - 82 * s);
      ctx.stroke();
      // Flag fabric — gentle wave
      ctx.beginPath();
      ctx.moveTo(cx + 5 * s, cy - 82 * s);
      ctx.bezierCurveTo(
        cx + 10 * s + flagWave, cy - 80 * s,
        cx + 16 * s - flagWave, cy - 76 * s,
        cx + 20 * s + flagWave * 0.5, cy - 74 * s
      );
      ctx.lineTo(cx + 5 * s, cy - 72 * s);
      ctx.closePath();
      ctx.fill();

      ctx.restore();
    }

    /* ── Shiva's crescent moon (secondary presence) ── */
    function drawMoon() {
      const mx = W * 0.20;
      const my = H * 0.08;
      const mr = Math.min(W, H) * 0.016;

      ctx.save();
      ctx.globalAlpha = 0.12 + Math.sin(t * 0.00025) * 0.025;

      // Glow
      const mg = ctx.createRadialGradient(mx, my, 0, mx, my, mr * 5);
      mg.addColorStop(0, "rgba(210, 200, 185, 0.22)");
      mg.addColorStop(0.5, "rgba(200, 190, 175, 0.06)");
      mg.addColorStop(1, "rgba(200, 190, 175, 0)");
      ctx.fillStyle = mg;
      ctx.beginPath();
      ctx.arc(mx, my, mr * 5, 0, Math.PI * 2);
      ctx.fill();

      // Crescent
      ctx.fillStyle = "rgba(225, 218, 205, 0.75)";
      ctx.beginPath();
      ctx.arc(mx, my, mr, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalCompositeOperation = "destination-out";
      ctx.beginPath();
      ctx.arc(mx + mr * 0.4, my - mr * 0.12, mr * 0.80, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalCompositeOperation = "source-over";

      ctx.restore();
    }

    /* ── Valley mist ── */
    function drawMist() {
      const my = H * 0.68;
      const g = ctx.createLinearGradient(0, my, 0, H);
      g.addColorStop(0, "rgba(230, 222, 208, 0)");
      g.addColorStop(0.15, "rgba(233, 226, 213, 0.06)");
      g.addColorStop(0.4, "rgba(238, 232, 220, 0.14)");
      g.addColorStop(0.7, "rgba(243, 238, 228, 0.28)");
      g.addColorStop(1, "rgba(248, 246, 242, 0.60)");
      ctx.fillStyle = g;
      ctx.fillRect(0, my, W, H - my);
    }

    /* ── Dust particles ── */
    function drawDust() {
      if (Math.random() < 0.018) spawnDust();
      dust = dust.filter((d) => d.life < d.maxLife);

      for (const d of dust) {
        d.x += d.vx + Math.sin(t * 0.0006 + d.phase) * 0.05;
        d.y += d.vy;
        d.life++;

        const fadeIn = Math.min(d.life / 50, 1);
        const fadeOut = Math.max(0, 1 - (d.life - d.maxLife + 60) / 60);
        d.opacity = fadeIn * fadeOut * 0.15;

        if (d.y < 0) d.opacity *= 0.2;

        ctx.beginPath();
        ctx.arc(d.x, d.y, d.size, 0, Math.PI * 2);
        const warm = Math.sin(t * 0.0006 + d.phase) * 0.5 + 0.5;
        ctx.fillStyle = `rgba(${215 + warm * 35}, ${195 + warm * 25}, ${155 + warm * 15}, ${d.opacity})`;
        ctx.fill();
      }
    }

    /* ════════════════════════════════════════════════════════════
       MAIN LOOP
       ════════════════════════════════════════════════════════════ */
    const animate = () => {
      t++;
      W = canvas.width;
      H = canvas.height;
      ctx.clearRect(0, 0, W, H);

      drawSky();
      drawSun();
      drawRays();
      drawMoon();
      drawClouds();
      drawMtn(farMtn);
      drawShiva();
      drawMtn(midMtn);
      drawTemple();
      drawChariot();
      drawMtn(nearMtn);
      drawMist();
      drawDust();

      // Bottom fade into page background
      const bf = ctx.createLinearGradient(0, H * 0.76, 0, H);
      bf.addColorStop(0, "rgba(248, 246, 242, 0)");
      bf.addColorStop(0.35, "rgba(248, 246, 242, 0.20)");
      bf.addColorStop(0.70, "rgba(248, 246, 242, 0.65)");
      bf.addColorStop(1, "rgba(248, 246, 242, 0.97)");
      ctx.fillStyle = bf;
      ctx.fillRect(0, H * 0.80, W, H * 0.20);

      rafRef.current = requestAnimationFrame(animate);
    };
    animate();

    const onResize = () => {
      dpr = setupCanvas(canvas);
      W = canvas.width;
      H = canvas.height;
      initTerrain();
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", onResize);
    };
  }, [setupCanvas]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none select-none"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    />
  );
}
