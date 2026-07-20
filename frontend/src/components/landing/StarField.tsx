"use client";

import { useEffect, useRef, useCallback } from "react";

interface Star {
  x: number; y: number;
  size: number; opacity: number;
  twinkleSpeed: number; twinklePhase: number;
  layer: number; hue: number;
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

interface FloatingLamp {
  x: number; y: number;
  size: number; opacity: number;
  driftX: number; driftSpeed: number;
  phase: number;
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

    let dpr = resize(canvas); // eslint-disable-line @typescript-eslint/no-unused-vars 
    const { w, h } = dimsRef.current;

    // ── Stars ──
    const starCount = Math.floor((w * h) / 7000);
    const stars: Star[] = Array.from({ length: starCount }, () => ({
      x: Math.random() * w, y: Math.random() * h,
      size: Math.random() * 1.6 + 0.2,
      opacity: Math.random() * 0.6 + 0.3,
      twinkleSpeed: Math.random() * 0.012 + 0.003,
      twinklePhase: Math.random() * Math.PI * 2,
      layer: Math.floor(Math.random() * 3),
      hue: Math.random() > 0.88 ? (Math.random() > 0.5 ? 40 : 260) : 0,
    }));

    // ── Constellations ──
    const conCount = 2;
    const constellations: Constellation[] = Array.from({ length: conCount }, () => {
      const cx = Math.random() * w * 0.5 + w * 0.25;
      const cy = Math.random() * h * 0.3 + h * 0.05;
      return {
        stars: Array.from({ length: 4 + Math.floor(Math.random() * 4) }, () => ({
          x: cx + (Math.random() - 0.5) * w * 0.12,
          y: cy + (Math.random() - 0.5) * h * 0.1,
        })),
        opacity: 0, phase: Math.random() * Math.PI * 2,
        speed: 0.003 + Math.random() * 0.003,
      };
    });

    // ── Floating particles ──
    let particles: Particle[] = [];
    const spawnParticle = () => {
      if (particles.length < 18) {
        const side = Math.floor(Math.random() * 4);
        particles.push({
          x: side === 0 ? Math.random() * w : side === 1 ? w : side === 2 ? Math.random() * w : 0,
          y: side === 0 ? 0 : side === 1 ? Math.random() * h : side === 2 ? h : Math.random() * h,
          vx: (Math.random() - 0.5) * 0.25,
          vy: (Math.random() - 0.5) * 0.25 - 0.08,
          size: Math.random() * 1.8 + 0.8,
          opacity: 0, hue: Math.random() > 0.5 ? 42 : 260,
          life: 0, maxLife: 400 + Math.random() * 400,
        });
      }
    };

    // ── Floating lamps (diya-inspired) ──
    let lamps: FloatingLamp[] = [];
    const spawnLamp = () => {
      lamps.push({
        x: Math.random() * w * 0.7 + w * 0.15,
        y: h + 20,
        size: 3 + Math.random() * 2,
        opacity: 0,
        driftX: (Math.random() - 0.5) * 0.15,
        driftSpeed: 0.15 + Math.random() * 0.1,
        phase: Math.random() * Math.PI * 2,
      });
    };

    // Initial lamps
    for (let i = 0; i < 6; i++) {
      lamps.push({
        x: Math.random() * w * 0.7 + w * 0.15,
        y: h - Math.random() * h * 0.6,
        size: 3 + Math.random() * 2,
        opacity: Math.random() * 0.4,
        driftX: (Math.random() - 0.5) * 0.15,
        driftSpeed: 0.15 + Math.random() * 0.1,
        phase: Math.random() * Math.PI * 2,
      });
    }

    // ── Sacred geometry ──
    const sacredGeo = {
      phase: 0,
      rings: [
        { radius: Math.min(w, h) * 0.10, speed: 0.008, opacity: 0.05 },
        { radius: Math.min(w, h) * 0.16, speed: -0.006, opacity: 0.04 },
        { radius: Math.min(w, h) * 0.22, speed: 0.009, opacity: 0.03 },
        { radius: Math.min(w, h) * 0.28, speed: -0.007, opacity: 0.02 },
      ],
    };
    const cx = w / 2, cy = h * 0.38;

    // ── Temple silhouette (procedural) ──
    const temple = {
      baseY: h * 0.85,
      width: Math.min(w * 0.35, 400),
      centerX: w / 2,
    };

    const animate = () => {
      timeRef.current += 0.01;
      const t = timeRef.current;
      ctx.clearRect(0, 0, w, h);

      // ── Deep background gradient ──
      const bgGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, h * 0.8);
      bgGrad.addColorStop(0, "rgba(15, 10, 30, 1)");
      bgGrad.addColorStop(0.4, "rgba(8, 6, 20, 1)");
      bgGrad.addColorStop(1, "rgba(4, 3, 12, 1)");
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, w, h);

      // ── Nebula glow 1 (top) ──
      const neb1 = ctx.createRadialGradient(cx, cy * 0.3, 0, cx, cy * 0.3, w * 0.45);
      neb1.addColorStop(0, "rgba(100, 60, 180, 0.018)");
      neb1.addColorStop(0.5, "rgba(60, 30, 120, 0.010)");
      neb1.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = neb1;
      ctx.fillRect(0, 0, w, h);

      // ── Nebula glow 2 (golden) ──
      const neb2 = ctx.createRadialGradient(w * 0.75, h * 0.65, 0, w * 0.75, h * 0.65, w * 0.35);
      neb2.addColorStop(0, "rgba(180, 120, 60, 0.012)");
      neb2.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = neb2;
      ctx.fillRect(0, 0, w, h);

      // ── Light rays from center ──
      for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 2 + t * 0.003;
        const rayLength = Math.min(w, h) * (0.35 + Math.sin(t * 0.005 + i) * 0.05);
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, rayLength);
        grad.addColorStop(0, `rgba(240, 176, 0, ${0.015 + Math.sin(t * 0.003 + i * 0.5) * 0.005})`);
        grad.addColorStop(1, "rgba(240, 176, 0, 0)");
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(angle);
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 2, rayLength);
        ctx.restore();
      }

      // ── Sacred geometry ──
      sacredGeo.phase += 0.008;
      for (const ring of sacredGeo.rings) {
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(t * ring.speed);
        ctx.strokeStyle = `rgba(240, 176, 0, ${ring.opacity})`;
        ctx.lineWidth = 0.4;
        ctx.beginPath();
        ctx.arc(0, 0, ring.radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      }

      // ── Lotus petal mandala ──
      const petalR = Math.min(w, h) * 0.07;
      const petalOpacity = 0.025 + Math.sin(t * 0.004) * 0.01;
      for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 2 + t * 0.002;
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(angle);
        ctx.beginPath();
        ctx.ellipse(petalR * 0.5, 0, petalR, petalR * 0.35, 0, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(200, 160, 80, ${petalOpacity})`;
        ctx.lineWidth = 0.3;
        ctx.stroke();
        ctx.restore();
      }

      // ── Stars ──
      for (const star of stars) {
        const twinkle = Math.sin(t * star.twinkleSpeed * 5 + star.twinklePhase) * 0.3 + 0.7;
        const alpha = star.opacity * twinkle;
        const ls = 1 + star.layer * 0.25;
        const color = star.hue === 0
          ? `rgba(255, 255, 255, ${alpha * 0.5 * ls})`
          : star.hue === 40
            ? `rgba(255, 200, 100, ${alpha * 0.6 * ls})`
            : `rgba(180, 140, 255, ${alpha * 0.6 * ls})`;
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size * ls, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        if (star.size > 1.2) {
          ctx.beginPath();
          ctx.arc(star.x, star.y, star.size * 3.5 * ls, 0, Math.PI * 2);
          ctx.fillStyle = star.hue === 0 ? `rgba(255,255,255,${alpha * 0.03})` : `rgba(255,200,100,${alpha * 0.04})`;
          ctx.fill();
        }
      }

      // ── Constellations ──
      for (const con of constellations) {
        con.opacity = Math.sin(t * con.speed + con.phase) * 0.12 + 0.10;
        if (con.opacity > 0.04) {
          ctx.strokeStyle = `rgba(200, 180, 255, ${con.opacity})`;
          ctx.lineWidth = 0.2;
          for (let i = 0; i < con.stars.length - 1; i++) {
            ctx.beginPath();
            ctx.moveTo(con.stars[i].x, con.stars[i].y);
            ctx.lineTo(con.stars[i + 1].x, con.stars[i + 1].y);
            ctx.stroke();
          }
          for (const s of con.stars) {
            ctx.beginPath();
            ctx.arc(s.x, s.y, 1.2, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(200, 180, 255, ${con.opacity * 0.4})`;
            ctx.fill();
          }
        }
      }

      // ── Floating particles ──
      if (Math.random() < 0.025) spawnParticle();
      particles = particles.filter(p => p.life < p.maxLife);
      for (const p of particles) {
        p.x += p.vx; p.y += p.vy; p.life++;
        p.opacity = Math.sin((p.life / p.maxLife) * Math.PI) * 0.35;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.hue === 42
          ? `rgba(240, 176, 0, ${p.opacity})`
          : `rgba(160, 120, 255, ${p.opacity})`;
        ctx.fill();
      }

      // ── Floating lamps ──
      lamps = lamps.filter(l => l.y > -50);
      if (Math.random() < 0.008 && lamps.length < 10) spawnLamp();
      for (const lamp of lamps) {
        lamp.y -= lamp.driftSpeed;
        lamp.x += lamp.driftX + Math.sin(t * 0.01 + lamp.phase) * 0.2;
        lamp.opacity = Math.min(lamp.opacity + 0.003, 0.5);

        // Lamp glow
        ctx.beginPath();
        const lampGrad = ctx.createRadialGradient(lamp.x, lamp.y, 0, lamp.x, lamp.y, lamp.size * 8);
        lampGrad.addColorStop(0, `rgba(255, 200, 100, ${lamp.opacity * 0.3})`);
        lampGrad.addColorStop(0.3, `rgba(240, 176, 0, ${lamp.opacity * 0.1})`);
        lampGrad.addColorStop(1, "rgba(240, 176, 0, 0)");
        ctx.fillStyle = lampGrad;
        ctx.arc(lamp.x, lamp.y, lamp.size * 8, 0, Math.PI * 2);
        ctx.fill();

        // Lamp body
        ctx.beginPath();
        ctx.arc(lamp.x, lamp.y, lamp.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 220, 150, ${lamp.opacity * 0.8})`;
        ctx.fill();

        // Lamp flame
        ctx.beginPath();
        ctx.arc(lamp.x, lamp.y - lamp.size * 0.3, lamp.size * 0.4, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 180, 50, ${lamp.opacity * 0.9})`;
        ctx.fill();
      }

      // ── Temple silhouette ──
      const tw = temple.width;
      const tx = temple.centerX;
      const ty = temple.baseY;

      ctx.fillStyle = "rgba(4, 3, 12, 0.85)";

      // Main body
      ctx.beginPath();
      ctx.moveTo(tx - tw * 0.15, ty);
      ctx.lineTo(tx - tw * 0.12, ty - tw * 0.45);
      ctx.lineTo(tx - tw * 0.08, ty - tw * 0.48);
      ctx.lineTo(tx - tw * 0.08, ty - tw * 0.55);
      ctx.lineTo(tx - tw * 0.10, ty - tw * 0.58);
      ctx.lineTo(tx - tw * 0.08, ty - tw * 0.60);
      ctx.lineTo(tx + tw * 0.08, ty - tw * 0.60);
      ctx.lineTo(tx + tw * 0.10, ty - tw * 0.58);
      ctx.lineTo(tx + tw * 0.08, ty - tw * 0.55);
      ctx.lineTo(tx + tw * 0.08, ty - tw * 0.48);
      ctx.lineTo(tx + tw * 0.12, ty - tw * 0.45);
      ctx.lineTo(tx + tw * 0.15, ty);
      ctx.closePath();
      ctx.fill();

      // Inner glow at temple base
      const templeGlow = ctx.createRadialGradient(tx, ty, 0, tx, ty, tw * 0.2);
      templeGlow.addColorStop(0, `rgba(240, 176, 0, ${0.04 + Math.sin(t * 0.002) * 0.02})`);
      templeGlow.addColorStop(1, "rgba(240, 176, 0, 0)");
      ctx.fillStyle = templeGlow;
      ctx.beginPath();
      ctx.arc(tx, ty, tw * 0.2, 0, Math.PI * 2);
      ctx.fill();

      // Pillars
      ctx.fillStyle = "rgba(6, 5, 16, 0.6)";
      for (let i = -2; i <= 2; i++) {
        const px = tx + i * tw * 0.035;
        const pw = tw * 0.015;
        const ph = tw * 0.25;
        ctx.fillRect(px - pw / 2, ty - ph, pw, ph);
      }

      // Horizontal bands
      ctx.fillStyle = "rgba(8, 6, 20, 0.4)";
      for (let i = 1; i <= 3; i++) {
        const bandY = ty - tw * 0.12 * i;
        ctx.fillRect(tx - tw * 0.12, bandY, tw * 0.24, 1.5);
      }

      animRef.current = requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => { dpr = resize(canvas); };
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
