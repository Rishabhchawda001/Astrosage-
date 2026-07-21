"use client";

import { useEffect, useRef, useCallback } from "react";

/* ════════════════════════════════════════════════════════════════
   AstroSage AI — Cinematic Hero Artwork
   Dawn on Kurukshetra — A procedural matte painting
   Krishna, Arjuna, the Four Horses, and the Presence of Shiva
   ════════════════════════════════════════════════════════════════ */

interface Cloud {
  x: number;
  y: number;
  w: number;
  h: number;
  speed: number;
  opacity: number;
  lobes: number;
  layer: number;
}

interface MtnLayer {
  pts: { x: number; y: number }[];
  color: string;
  haze: string;
  parallax: number;
}

interface Dust {
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
  const ref = useRef<HTMLCanvasElement>(null);
  const raf = useRef<number>(0);

  const size = useCallback((c: HTMLCanvasElement) => {
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
    const c = ref.current;
    if (!c) return;
    let dpr = size(c);
    const x = c.getContext("2d")!;
    let t = 0;
    let W = c.width;
    let H = c.height;

    /* ── Terrain ── */
    function peaks(by: number, n: number, a: number, s: number) {
      const p: { x: number; y: number }[] = [];
      const step = W / (n - 1);
      for (let i = 0; i < n; i++) {
        const px = i * step;
        const noise =
          Math.sin(i * 1.7 + s) * 0.32 +
          Math.sin(i * 3.1 + s * 2) * 0.18 +
          Math.sin(i * 0.5 + s * 0.7) * 0.32 +
          Math.cos(i * 2.3 + s * 1.3) * 0.10 +
          Math.sin(i * 4.7 + s * 0.4) * 0.08;
        const bell = Math.sin((i / (n - 1)) * Math.PI);
        p.push({ x: px, y: by * H + noise * a * H + bell * a * H * 0.22 });
      }
      return p;
    }

    let far: MtnLayer = { pts: [], color: "rgba(148,140,128,0.16)", haze: "rgba(180,175,168,0.08)", parallax: 0.0012 };
    let mid1: MtnLayer = { pts: [], color: "rgba(120,112,98,0.22)", haze: "rgba(160,152,140,0.06)", parallax: 0.003 };
    let mid2: MtnLayer = { pts: [], color: "rgba(95,86,74,0.30)", haze: "rgba(130,120,108,0.05)", parallax: 0.006 };
    let near: MtnLayer = { pts: [], color: "rgba(65,58,48,0.42)", haze: "rgba(100,90,78,0.04)", parallax: 0.009 };

    function initTerrain() {
      if (!c) return;
      W = c.width; H = c.height;
      far.pts = peaks(0.56, 18, 0.05, 42);
      mid1.pts = peaks(0.62, 16, 0.048, 17);
      mid2.pts = peaks(0.68, 14, 0.045, 73);
      near.pts = peaks(0.76, 12, 0.035, 55);
    }
    initTerrain();

    /* ── Clouds ── */
    const clouds: Cloud[] = [];
    for (let i = 0; i < 10; i++) {
      clouds.push({
        x: Math.random() * 2.8 - 0.9,
        y: 0.04 + Math.random() * 0.28,
        w: 0.06 + Math.random() * 0.14,
        h: 0.008 + Math.random() * 0.015,
        speed: 0.000012 + Math.random() * 0.000020,
        opacity: 0.04 + Math.random() * 0.08,
        lobes: 2 + Math.floor(Math.random() * 3),
        layer: Math.floor(Math.random() * 3),
      });
    }

    /* ── Dust ── */
    let dust: Dust[] = [];
    function spawnDust() {
      dust.push({
        x: Math.random() * W,
        y: H * 0.28 + Math.random() * H * 0.58,
        sz: 0.5 + Math.random() * 1.4,
        op: 0,
        vx: (Math.random() - 0.5) * 0.08,
        vy: -(0.02 + Math.random() * 0.06),
        ph: Math.random() * Math.PI * 2,
        life: 0,
        max: 220 + Math.random() * 280,
      });
    }

    /* ════════════════════════════════════════════════════════════
       RENDERING
       ════════════════════════════════════════════════════════════ */

    function drawSky() {
      const g = x.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0.00, "#b5afa5");
      g.addColorStop(0.08, "#c2bbb0");
      g.addColorStop(0.18, "#d0c8bc");
      g.addColorStop(0.30, "#dcd4c6");
      g.addColorStop(0.44, "#e6dccb");
      g.addColorStop(0.56, "#ede2cc");
      g.addColorStop(0.68, "#f0e4c8");
      g.addColorStop(0.78, "#ecd2a2");
      g.addColorStop(0.88, "#e2c078");
      g.addColorStop(0.95, "#d8b060");
      g.addColorStop(1.00, "#cca048");
      x.fillStyle = g;
      x.fillRect(0, 0, W, H);
    }

    function drawSun() {
      const sx = W * 0.57;
      const sy = H * 0.53;
      const sr = Math.min(W, H) * 0.050;

      // Outer atmospheric scatter
      const atmo = x.createRadialGradient(sx, sy, 0, sx, sy, sr * 8);
      atmo.addColorStop(0, "rgba(255,220,145,0.18)");
      atmo.addColorStop(0.2, "rgba(255,212,128,0.09)");
      atmo.addColorStop(0.5, "rgba(255,202,108,0.03)");
      atmo.addColorStop(1, "rgba(255,192,88,0)");
      x.fillStyle = atmo;
      x.fillRect(0, 0, W, H);

      // Core disc
      const sg = x.createRadialGradient(sx, sy, 0, sx, sy, sr);
      sg.addColorStop(0, "rgba(255,230,165,0.80)");
      sg.addColorStop(0.35, "rgba(255,218,145,0.48)");
      sg.addColorStop(0.70, "rgba(255,205,120,0.15)");
      sg.addColorStop(1, "rgba(255,190,95,0)");
      x.fillStyle = sg;
      x.beginPath();
      x.arc(sx, sy, sr, 0, Math.PI * 2);
      x.fill();
    }

    function drawRays() {
      const sx = W * 0.57;
      const sy = H * 0.53;
      x.save();
      x.globalAlpha = 0.026 + Math.sin(t * 0.0003) * 0.006;
      for (let i = 0; i < 16; i++) {
        const a = (i / 16) * Math.PI * 0.70 - 0.14;
        const len = H * 0.88;
        x.beginPath();
        x.moveTo(sx, sy);
        x.lineTo(sx + Math.cos(a - 0.010) * len, sy + Math.sin(a - 0.010) * len);
        x.lineTo(sx + Math.cos(a + 0.010) * len, sy + Math.sin(a + 0.010) * len);
        x.closePath();
        const rg = x.createLinearGradient(sx, sy, sx + Math.cos(a) * len, sy + Math.sin(a) * len);
        rg.addColorStop(0, "rgba(255,222,155,0.40)");
        rg.addColorStop(0.20, "rgba(255,212,135,0.15)");
        rg.addColorStop(1, "rgba(255,200,115,0)");
        x.fillStyle = rg;
        x.fill();
      }
      x.restore();
    }

    function drawClouds(beforeMtn: boolean) {
      for (const cl of clouds) {
        if (beforeMtn ? cl.layer > 0 : cl.layer === 0) continue;
        cl.x += cl.speed;
        if (cl.x > 2.5) cl.x = -cl.w - 0.4;

        const cx = cl.x * W;
        const cy = cl.y * H;
        const cw = cl.w * W;
        const ch = cl.h * H;

        x.save();
        x.globalAlpha = cl.opacity + Math.sin(t * 0.00012 + cl.x * 10) * 0.012;
        const cg = x.createRadialGradient(cx, cy, 0, cx, cy, cw * 0.45);
        cg.addColorStop(0, "rgba(236,230,220,0.70)");
        cg.addColorStop(0.5, "rgba(232,226,214,0.30)");
        cg.addColorStop(1, "rgba(228,220,208,0)");
        x.fillStyle = cg;

        for (let l = 0; l < cl.lobes; l++) {
          const lx = cx + (l - (cl.lobes - 1) / 2) * cw * 0.20;
          const ly = cy - ch * 0.12 * Math.sin(l * 2.1);
          x.beginPath();
          x.ellipse(lx, ly, cw * (0.32 - l * 0.015), ch * (0.75 - l * 0.04), 0, 0, Math.PI * 2);
          x.fill();
        }
        x.restore();
      }
    }

    function drawMtn(layer: MtnLayer) {
      const pts = layer.pts;
      const off = Math.sin(t * 0.00012) * layer.parallax * W * 0.20;
      x.save();
      x.fillStyle = layer.color;
      x.beginPath();
      x.moveTo(pts[0].x + off, pts[0].y);
      for (let i = 1; i < pts.length; i++) {
        const p = pts[i - 1];
        const q = pts[i];
        x.quadraticCurveTo(p.x + off, p.y, (p.x + q.x) / 2 + off, (p.y + q.y) / 2);
      }
      x.lineTo(pts[pts.length - 1].x + off, pts[pts.length - 1].y);
      x.lineTo(W + 10, H + 10);
      x.lineTo(-10, H + 10);
      x.closePath();
      x.fill();

      // Atmospheric haze overlay
      if (layer.haze) {
        x.fillStyle = layer.haze;
        x.fill();
      }
      x.restore();
    }

    /* ── Shiva: meditation figure on distant Himalayan peak ── */
    function drawShiva() {
      const px = W * 0.13;
      const py = H * 0.50;
      const s = Math.min(W, H) * 0.00042;

      x.save();
      x.fillStyle = "rgba(115,108,95,0.20)";

      // Seated body — broad base, tapering torso
      x.beginPath();
      x.moveTo(px - 20 * s, py + 4 * s);
      x.bezierCurveTo(px - 22 * s, py - 6 * s, px - 18 * s, py - 20 * s, px - 10 * s, py - 30 * s);
      x.bezierCurveTo(px - 5 * s, py - 36 * s, px - 2 * s, py - 40 * s, px, py - 42 * s);
      x.bezierCurveTo(px + 2 * s, py - 40 * s, px + 5 * s, py - 36 * s, px + 10 * s, py - 30 * s);
      x.bezierCurveTo(px + 18 * s, py - 20 * s, px + 22 * s, py - 6 * s, px + 20 * s, py + 4 * s);
      x.closePath();
      x.fill();

      // Head
      x.beginPath();
      x.arc(px, py - 46 * s, 5.5 * s, 0, Math.PI * 2);
      x.fill();

      // Jata (matted hair)
      x.beginPath();
      x.moveTo(px - 4 * s, py - 50 * s);
      x.bezierCurveTo(px - 3 * s, py - 58 * s, px + 1 * s, py - 62 * s, px + 4 * s, py - 55 * s);
      x.bezierCurveTo(px + 5 * s, py - 52 * s, px + 4 * s, py - 50 * s, px + 4 * s, py - 50 * s);
      x.closePath();
      x.fill();

      // Trishula
      x.strokeStyle = "rgba(115,108,95,0.18)";
      x.lineWidth = 1.0 * s;
      x.beginPath();
      x.moveTo(px + 24 * s, py + 6 * s);
      x.lineTo(px + 24 * s, py - 58 * s);
      x.stroke();
      // Prongs
      x.beginPath();
      x.moveTo(px + 20 * s, py - 58 * s);
      x.lineTo(px + 24 * s, py - 66 * s);
      x.lineTo(px + 28 * s, py - 58 * s);
      x.stroke();
      x.beginPath();
      x.moveTo(px + 24 * s, py - 54 * s);
      x.lineTo(px + 24 * s, py - 64 * s);
      x.stroke();

      // Nandi (bull) silhouette beside Shiva
      x.fillStyle = "rgba(115,108,95,0.15)";
      x.beginPath();
      x.moveTo(px - 30 * s, py + 6 * s);
      x.bezierCurveTo(px - 34 * s, py, px - 38 * s, py - 4 * s, px - 40 * s, py - 2 * s);
      x.bezierCurveTo(px - 42 * s, py, px - 40 * s, py + 4 * s, px - 36 * s, py + 6 * s);
      x.lineTo(px - 30 * s, py + 6 * s);
      x.closePath();
      x.fill();
      // Nandi head
      x.beginPath();
      x.arc(px - 42 * s, py - 4 * s, 2.5 * s, 0, Math.PI * 2);
      x.fill();

      // Divine glow
      x.globalAlpha = 0.05 + Math.sin(t * 0.00022) * 0.015;
      const sg = x.createRadialGradient(px, py - 46 * s, 0, px, py - 46 * s, 32 * s);
      sg.addColorStop(0, "rgba(205,200,188,0.35)");
      sg.addColorStop(0.5, "rgba(200,195,182,0.10)");
      sg.addColorStop(1, "rgba(200,195,182,0)");
      x.fillStyle = sg;
      x.beginPath();
      x.arc(px, py - 46 * s, 32 * s, 0, Math.PI * 2);
      x.fill();

      x.restore();
    }

    /* ── Temple ── */
    function drawTemple() {
      const tx = W * 0.40;
      const by = H * 0.66;
      const s = Math.min(W, H) * 0.00065;

      x.save();
      x.fillStyle = "rgba(55,48,38,0.45)";

      // Shikhara
      x.beginPath();
      x.moveTo(tx - 15 * s, by);
      x.lineTo(tx - 9 * s, by - 52 * s);
      x.lineTo(tx - 5 * s, by - 78 * s);
      x.lineTo(tx - 2.5 * s, by - 95 * s);
      x.lineTo(tx, by - 106 * s);
      x.lineTo(tx + 2.5 * s, by - 95 * s);
      x.lineTo(tx + 5 * s, by - 78 * s);
      x.lineTo(tx + 9 * s, by - 52 * s);
      x.lineTo(tx + 15 * s, by);
      x.closePath();
      x.fill();

      // Mandapa base
      x.fillRect(tx - 24 * s, by, 48 * s, 5 * s);

      // Pillars
      x.fillRect(tx - 18 * s, by - 26 * s, 2.2 * s, 26 * s);
      x.fillRect(tx + 15.8 * s, by - 26 * s, 2.2 * s, 26 * s);

      // Kalasha
      x.beginPath();
      x.arc(tx, by - 109 * s, 2.2 * s, 0, Math.PI * 2);
      x.fill();

      // Spire glow
      x.globalAlpha = 0.18 + Math.sin(t * 0.00045) * 0.05;
      const sg = x.createRadialGradient(tx, by - 95 * s, 0, tx, by - 95 * s, 20 * s);
      sg.addColorStop(0, "rgba(212,160,48,0.30)");
      sg.addColorStop(1, "rgba(212,160,48,0)");
      x.fillStyle = sg;
      x.beginPath();
      x.arc(tx, by - 95 * s, 20 * s, 0, Math.PI * 2);
      x.fill();

      x.restore();
    }

    /* ── Krishna's Chariot ── */
    function drawChariot() {
      const cx = W * 0.73;
      const cy = H * 0.73;
      const s = Math.min(W, H) * 0.00052;

      x.save();

      /* Four horses — white/silver */
      x.fillStyle = "rgba(205,200,190,0.48)";
      for (let i = 0; i < 4; i++) {
        const hx = cx - 12 * s - i * 9 * s;
        const hy = cy - 5 * s;

        // Body
        x.beginPath();
        x.moveTo(hx, hy);
        x.bezierCurveTo(hx - 7 * s, hy - 9 * s, hx - 18 * s, hy - 12 * s, hx - 25 * s, hy - 9 * s);
        x.bezierCurveTo(hx - 27 * s, hy - 7 * s, hx - 27 * s, hy - 2 * s, hx - 23 * s, hy + 2 * s);
        x.lineTo(hx + 2 * s, hy + 2 * s);
        x.closePath();
        x.fill();

        // Neck + head
        x.beginPath();
        x.moveTo(hx - 21 * s, hy - 9 * s);
        x.bezierCurveTo(hx - 27 * s, hy - 20 * s, hx - 30 * s, hy - 24 * s, hx - 32 * s, hy - 20 * s);
        x.bezierCurveTo(hx - 33 * s, hy - 18 * s, hx - 31 * s, hy - 14 * s, hx - 27 * s, hy - 12 * s);
        x.closePath();
        x.fill();

        // Legs
        x.fillRect(hx - 23 * s, hy + 2 * s, 1.0 * s, 5.5 * s);
        x.fillRect(hx - 16 * s, hy + 2 * s, 1.0 * s, 5.0 * s);
        x.fillRect(hx - 5 * s, hy + 2 * s, 1.0 * s, 5.5 * s);
        x.fillRect(hx + 0 * s, hy + 2 * s, 1.0 * s, 5.0 * s);

        // Tail wisps
        x.strokeStyle = "rgba(205,200,190,0.30)";
        x.lineWidth = 0.6 * s;
        x.beginPath();
        x.moveTo(hx + 2 * s, hy - 2 * s);
        x.bezierCurveTo(hx + 6 * s, hy - 4 * s, hx + 8 * s, hy - 1 * s, hx + 10 * s, hy - 3 * s);
        x.stroke();
      }

      /* Chariot body */
      x.fillStyle = "rgba(60,52,40,0.48)";
      x.beginPath();
      x.moveTo(cx - 7 * s, cy);
      x.lineTo(cx + 30 * s, cy);
      x.lineTo(cx + 32 * s, cy - 13 * s);
      x.lineTo(cx - 5 * s, cy - 13 * s);
      x.closePath();
      x.fill();

      // Rail
      x.strokeStyle = "rgba(75,65,48,0.30)";
      x.lineWidth = 0.8 * s;
      x.beginPath();
      x.moveTo(cx - 5 * s, cy - 13 * s);
      x.lineTo(cx + 32 * s, cy - 13 * s);
      x.stroke();

      // Wheels
      x.fillStyle = "rgba(60,52,40,0.42)";
      x.beginPath();
      x.arc(cx, cy + 4 * s, 4 * s, 0, Math.PI * 2);
      x.fill();
      x.beginPath();
      x.arc(cx + 22 * s, cy + 4 * s, 4 * s, 0, Math.PI * 2);
      x.fill();

      /* Krishna — tall, commanding */
      x.fillStyle = "rgba(50,44,35,0.50)";

      x.beginPath();
      x.moveTo(cx + 2 * s, cy - 13 * s);
      x.lineTo(cx + 1 * s, cy - 42 * s);
      x.bezierCurveTo(cx + 1 * s, cy - 46 * s, cx + 3 * s, cy - 50 * s, cx + 5 * s, cy - 50 * s);
      x.bezierCurveTo(cx + 7 * s, cy - 50 * s, cx + 9 * s, cy - 46 * s, cx + 9 * s, cy - 42 * s);
      x.lineTo(cx + 8 * s, cy - 13 * s);
      x.closePath();
      x.fill();

      // Head
      x.beginPath();
      x.arc(cx + 5 * s, cy - 53 * s, 4.2 * s, 0, Math.PI * 2);
      x.fill();

      // Mukuta (crown)
      x.beginPath();
      x.moveTo(cx + 1 * s, cy - 56 * s);
      x.lineTo(cx + 5 * s, cy - 64 * s);
      x.lineTo(cx + 9 * s, cy - 56 * s);
      x.closePath();
      x.fill();

      // Peacock feather
      x.strokeStyle = "rgba(50,44,35,0.30)";
      x.lineWidth = 0.7 * s;
      x.beginPath();
      x.arc(cx + 5 * s, cy - 66 * s, 1.8 * s, -0.6, Math.PI + 0.6);
      x.stroke();

      /* Arjuna — seated, reverent */
      x.fillStyle = "rgba(50,44,35,0.45)";

      x.beginPath();
      x.moveTo(cx + 13 * s, cy - 13 * s);
      x.lineTo(cx + 14 * s, cy - 30 * s);
      x.bezierCurveTo(cx + 14 * s, cy - 34 * s, cx + 16 * s, cy - 36 * s, cx + 18 * s, cy - 36 * s);
      x.bezierCurveTo(cx + 20 * s, cy - 36 * s, cx + 22 * s, cy - 34 * s, cx + 22 * s, cy - 30 * s);
      x.lineTo(cx + 23 * s, cy - 13 * s);
      x.closePath();
      x.fill();

      // Head
      x.beginPath();
      x.arc(cx + 18 * s, cy - 38 * s, 3.5 * s, 0, Math.PI * 2);
      x.fill();

      /* Dharma flag */
      const wave = Math.sin(t * 0.0018) * 1.8 * s;
      x.fillStyle = "rgba(50,44,35,0.38)";
      x.strokeStyle = "rgba(50,44,35,0.40)";
      x.lineWidth = 1.0 * s;
      x.beginPath();
      x.moveTo(cx + 5 * s, cy - 64 * s);
      x.lineTo(cx + 5 * s, cy - 80 * s);
      x.stroke();
      x.beginPath();
      x.moveTo(cx + 5 * s, cy - 80 * s);
      x.bezierCurveTo(
        cx + 10 * s + wave, cy - 78 * s,
        cx + 15 * s - wave, cy - 74 * s,
        cx + 19 * s + wave * 0.5, cy - 72 * s
      );
      x.lineTo(cx + 5 * s, cy - 70 * s);
      x.closePath();
      x.fill();

      x.restore();
    }

    /* ── Crescent moon ── */
    function drawMoon() {
      const mx = W * 0.19;
      const my = H * 0.07;
      const mr = Math.min(W, H) * 0.014;

      x.save();
      x.globalAlpha = 0.10 + Math.sin(t * 0.00022) * 0.02;

      const mg = x.createRadialGradient(mx, my, 0, mx, my, mr * 5);
      mg.addColorStop(0, "rgba(208,198,182,0.20)");
      mg.addColorStop(0.5, "rgba(198,188,172,0.05)");
      mg.addColorStop(1, "rgba(198,188,172,0)");
      x.fillStyle = mg;
      x.beginPath();
      x.arc(mx, my, mr * 5, 0, Math.PI * 2);
      x.fill();

      x.fillStyle = "rgba(222,215,202,0.70)";
      x.beginPath();
      x.arc(mx, my, mr, 0, Math.PI * 2);
      x.fill();
      x.globalCompositeOperation = "destination-out";
      x.beginPath();
      x.arc(mx + mr * 0.4, my - mr * 0.10, mr * 0.78, 0, Math.PI * 2);
      x.fill();
      x.globalCompositeOperation = "source-over";

      x.restore();
    }

    /* ── Mist ── */
    function drawMist() {
      const my = H * 0.66;
      const g = x.createLinearGradient(0, my, 0, H);
      g.addColorStop(0, "rgba(228,220,206,0)");
      g.addColorStop(0.12, "rgba(230,224,212,0.05)");
      g.addColorStop(0.35, "rgba(236,230,218,0.12)");
      g.addColorStop(0.65, "rgba(242,238,228,0.25)");
      g.addColorStop(1, "rgba(248,246,242,0.55)");
      x.fillStyle = g;
      x.fillRect(0, my, W, H - my);
    }

    /* ── Dust ── */
    function drawDust() {
      if (Math.random() < 0.015) spawnDust();
      dust = dust.filter((d) => d.life < d.max);

      for (const d of dust) {
        d.x += d.vx + Math.sin(t * 0.0005 + d.ph) * 0.04;
        d.y += d.vy;
        d.life++;

        const fi = Math.min(d.life / 55, 1);
        const fo = Math.max(0, 1 - (d.life - d.max + 65) / 65);
        d.op = fi * fo * 0.12;

        if (d.y < 0) d.op *= 0.15;

        x.beginPath();
        x.arc(d.x, d.y, d.sz, 0, Math.PI * 2);
        const w = Math.sin(t * 0.0005 + d.ph) * 0.5 + 0.5;
        x.fillStyle = `rgba(${212 + w * 38},${192 + w * 28},${152 + w * 18},${d.op})`;
        x.fill();
      }
    }

    /* ── Cinematic color grade (film look) ── */
    function applyGrade() {
      // Warm highlight tint
      x.save();
      x.globalAlpha = 0.025;
      x.fillStyle = "#d4a030";
      x.fillRect(0, 0, W, H);
      x.restore();

      // Subtle vignette
      const vg = x.createRadialGradient(W * 0.5, H * 0.45, W * 0.25, W * 0.5, H * 0.5, W * 0.75);
      vg.addColorStop(0, "rgba(0,0,0,0)");
      vg.addColorStop(1, "rgba(0,0,0,0.08)");
      x.fillStyle = vg;
      x.fillRect(0, 0, W, H);
    }

    /* ════════════════════════════════════════════════════════════
       MAIN LOOP
       ════════════════════════════════════════════════════════════ */
    const animate = () => {
      t++;
      W = c.width;
      H = c.height;
      x.clearRect(0, 0, W, H);

      drawSky();
      drawSun();
      drawRays();
      drawMoon();
      drawClouds(true);
      drawMtn(far);
      drawShiva();
      drawMtn(mid1);
      drawClouds(false);
      drawTemple();
      drawChariot();
      drawMtn(mid2);
      drawMtn(near);
      drawMist();
      drawDust();
      applyGrade();

      // Bottom fade
      const bf = x.createLinearGradient(0, H * 0.75, 0, H);
      bf.addColorStop(0, "rgba(248,246,242,0)");
      bf.addColorStop(0.30, "rgba(248,246,242,0.18)");
      bf.addColorStop(0.65, "rgba(248,246,242,0.60)");
      bf.addColorStop(1, "rgba(248,246,242,0.97)");
      x.fillStyle = bf;
      x.fillRect(0, H * 0.80, W, H * 0.20);

      raf.current = requestAnimationFrame(animate);
    };
    animate();

    const onResize = () => {
      dpr = size(c);
      W = c.width;
      H = c.height;
      initTerrain();
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf.current);
      window.removeEventListener("resize", onResize);
    };
  }, [size]);

  return (
    <canvas
      ref={ref}
      className="fixed inset-0 w-full h-full pointer-events-none select-none"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    />
  );
}
