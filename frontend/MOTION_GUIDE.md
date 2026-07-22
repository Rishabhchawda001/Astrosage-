# AstroSage Motion Guide v2.0

## Philosophy

Motion in AstroSage is **meaningful, not decorative**. Every animation serves a purpose:
- Guide attention
- Communicate state changes
- Create spatial relationships
- Establish rhythm and flow

**Nothing distracting. Everything purposeful.**

---

## Duration Scale

| Token | Value | When to Use |
|-------|-------|-------------|
| `duration-fast` | 120ms | Hover states, button feedback |
| `duration-normal` | 200ms | Standard transitions, focus rings |
| `duration-slow` | 350ms | Page transitions, drawer slides |
| `duration-slower` | 500ms | Complex entrance animations |
| `duration-slowest` | 700ms | Hero entrances, cinematic moments |

---

## Easing Curves

| Name | Curve | Usage |
|------|-------|-------|
| `ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Most transitions — fast start, gentle settle |
| `ease-in-out` | `cubic-bezier(0.65, 0, 0.35, 1)` | Bidirectional movements |
| `ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Bouncy, playful entrances |

---

## Animation Patterns

### 1. Entrance (fade-in-up)
The primary entrance pattern. Elements fade in while moving upward.

```tsx
initial={{ opacity: 0, y: 12 }}
animate={{ opacity: 1, y: 0 }}
transition={{ duration: 0.6, ease: "easeOut" }}
```

**Translation**: 12px (subtle) to 16px (standard)

### 2. Staggered Entrance
Multiple elements enter in sequence with delays.

```tsx
// Parent
transition={{ staggerChildren: 0.1, delayChildren: 0.15 }}

// Children
transition={{ duration: 0.7, ease: "easeOut" }}
```

**Delay**: 80-100ms between siblings

### 3. Scroll Reveal
Elements enter when they scroll into view.

```tsx
const ref = useRef(null);
const inView = useInView(ref, { once: true, margin: "-50px" });

<motion.div
  ref={ref}
  initial={{ opacity: 0, y: 20 }}
  animate={inView ? { opacity: 1, y: 0 } : {}}
  transition={{ duration: 0.5, ease: "easeOut" }}
/>
```

**Margin**: -50px (triggers slightly before fully visible)

### 4. Drawer Slide
Side panels slide in from the edge.

```tsx
initial={{ x: "100%" }}
animate={{ x: 0 }}
exit={{ x: "100%" }}
transition={{ type: "spring", damping: 30, stiffness: 300 }}
```

### 5. Hover Lift
Cards lift slightly on hover with enhanced shadow.

```css
.card-premium:hover {
  box-shadow: var(--shadow-lg), var(--shadow-glow);
  transform: translateY(-2px);
}
```

### 6. Scale Feedback
Buttons scale slightly on press.

```css
.btn-primary:active {
  transform: translateY(0);
}
```

---

## Canvas Animations

### Home Page: CinematicBackground
- **Target**: 60fps
- **DPR cap**: 2
- **Elements**: Sacred geometry, river waves, light rays, mountains, particles, mist, vignette
- **Performance**: requestAnimationFrame, cleared each frame
- **Reduced motion**: Disables particles and geometry, keeps mountains/mist/vignette

### Other Pages: StarField
- **Target**: 60fps
- **DPR cap**: 2
- **Elements**: Sparse gold particles, warm gradient
- **Performance**: Pauses when not visible (IntersectionObserver)
- **Particle limit**: 15 max

### Knowledge Graph: GraphPreview
- **Target**: 60fps
- **Elements**: Force-directed physics, nodes, edges, labels
- **Performance**: requestAnimationFrame, DPR-aware

---

## Reduced Motion

All animations respect `prefers-reduced-motion: reduce`:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  .reveal {
    opacity: 1;
    transform: none;
  }
  html { scroll-behavior: auto; }
}
```

Canvas backgrounds check via JavaScript:
```js
const prefersReducedMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)"
).matches;
```

---

## What NOT to Do

- ❌ No bouncing or elastic animations (too playful)
- ❌ No spin/rotate on UI elements (distracting)
- ❌ No parallax scrolling (dated pattern)
- ❌ No loading spinners for instant operations
- ❌ No notification toasts for non-critical events
- ❌ No animated backgrounds on inner pages (performance)
- ❌ No cursor trails or mouse-following effects

---

*Generated: 2026-07-22*
