# AstroSage AI — Design System

## Purpose

This document is AstroSage's permanent visual constitution. Every UI decision must comply with it. Deviations require explicit justification documented in code comments.

---

## 1. Visual Philosophy

AstroSage is not software. It is a gateway to timeless knowledge. The interface must feel like entering a premium ancient library that happens to be powered by modern engineering.

**Core emotions**: Trust · Calm · Wisdom · Timelessness · Reverence

**Anti-patterns**: No neon. No gaming aesthetics. No heavy gradients. No clutter. No flashiness. No template feel.

---

## 2. Color Tokens

### Surfaces
| Token | Value | Usage |
|-------|-------|-------|
| `surface` | `#f8f6f2` | Page background |
| `surface-elevated` | `#ffffff` | Cards, elevated elements |
| `surface-overlay` | `rgba(255,255,255,0.85)` | Modal overlays, glass panels |

### Text
| Token | Value | Usage |
|-------|-------|-------|
| `text-primary` | `#2c2418` | Headlines, body |
| `text-secondary` | `#6b5d4f` | Descriptions |
| `text-tertiary` | `#9a8b7a` | Captions, labels |

### Accent — Gold
| Token | Value | Usage |
|-------|-------|-------|
| `gold-50` | `#fefcf5` | Tinted backgrounds |
| `gold-100` | `#fdf5e0` | Hover states |
| `gold-300` | `#f5d68a` | Highlights |
| `gold-500` | `#d4a030` | Primary accent, buttons |
| `gold-600` | `#b88820` | Hover accent |
| `gold-700` | `#9a6e18` | Active accent |

### Accent — Sacred
| Token | Value | Usage |
|-------|-------|-------|
| `sacred-500` | `#7a56e0` | Subtle spiritual accents |
| `sacred-400` | `#9a7aff` | Decorative glow |

### Semantic
| Token | Value | Usage |
|-------|-------|-------|
| `success` | `#4a9e6a` | Quality gates, positive |
| `error` | `#c45050` | Errors, low confidence |
| `warning` | `#d4a030` | Warnings |

### Borders
| Token | Value | Usage |
|-------|-------|-------|
| `border` | `rgba(60,45,30,0.08)` | Default dividers |
| `border-light` | `rgba(60,45,30,0.15)` | Subtle emphasis |

---

## 3. Typography

### Typefaces
- **Display / Headlines**: Cormorant Garamond — serif, elegant, museum-quality
- **Body / UI**: Inter — clean, modern, excellent readability

### Scale (Desktop)
| Level | Size | Weight | Font | Line-height |
|-------|------|--------|------|-------------|
| Hero | `text-7xl` (72px) | Bold | Serif | 1.1 |
| Section title | `text-4xl`–`text-5xl` | Bold | Serif | 1.15 |
| Card title | `text-xl` | Semibold | Serif | 1.3 |
| Body large | `text-lg` | Normal | Sans | 1.6 |
| Body | `text-base` | Normal | Sans | 1.6 |
| Small | `text-sm` | Normal | Sans | 1.5 |
| Caption | `text-xs` | Medium | Sans | 1.4 |

### Rules
- Headlines always use serif font
- Body text never exceeds 680px width for readability
- Gold gradient text for emphasis only on key words (max 1-2 per heading)
- Letter spacing: tight on headings (`tracking-tight`), normal on body

---

## 4. Spacing Scale

Base unit: `4px` (Tailwind default)

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | `4px` | Tight gaps |
| `sm` | `8px` | Icon gaps |
| `md` | `16px` | Card padding |
| `lg` | `24px` | Section gaps |
| `xl` | `32px` | Card internal spacing |
| `2xl` | `48px` | Section padding |
| `3xl` | `64px` | Major section spacing |
| `4xl` | `128px` | Hero spacing |

---

## 5. Elevation & Glass

### Shadows
```css
shadow-sm:  0 1px 3px rgba(60,45,30,0.04)
shadow-md:  0 4px 12px rgba(60,45,30,0.06)
shadow-lg:  0 8px 32px rgba(60,45,30,0.06)
```

### Glass
```css
glass:       bg-white/50 + blur(20px) + border
glass-strong: bg-white/75 + blur(32px) + border
glass-warm:  bg-[#fcf9f2]/70 + blur(24px) + gold border
```

### Cards
- `card-premium`: white, rounded-2xl, shadow-md, border, hover shadow-gold glow
- No dark backgrounds on landing page
- Warm shadows only (brown-tinted, never blue/black)

---

## 6. Buttons

### Primary
- Gold gradient background (`gold-500` → `gold-600`)
- White text, semibold
- Rounded-xl, generous padding
- Hover: lift (-1px), stronger shadow, brighter gradient
- Active: settle back

### Secondary
- White glass background, border
- Dark text
- Hover: brighter white, gold border tint

### CTA (Hero)
- Primary style, larger (px-10 py-5, text-lg)

---

## 7. Motion

### Duration
| Type | Duration | Easing |
|------|----------|--------|
| Micro | 150ms | ease-out |
| Standard | 300ms | ease-out |
| Entrance | 600ms | ease-out |
| Cinematic | 800ms | ease-out |

### Rules
- Entrance animations: fade-in-up (8-20px translation)
- Stagger delays: 80-100ms between sibling elements
- Scroll reveals: `useInView` with `once: true`, margin `-80px`
- Background canvas: continuous, 60fps target, never blocks interaction
- `prefers-reduced-motion`: disable all animations except canvas background

### Canvas Background
- Never animate deity figures
- Animate: clouds, light rays, dust particles, mist, parallax
- Cloud speed: imperceptibly slow drift
- Particles: gentle upward float with sine drift
- Light rays: subtle opacity pulsing (4-6% alpha)

---

## 8. Border Radius

| Element | Radius |
|---------|--------|
| Buttons | `rounded-xl` (12px) |
| Cards | `rounded-2xl` (16px) |
| Nav pill | `rounded-2xl` (16px) |
| Badges | `rounded-full` |
| Icons | `rounded-xl` |

---

## 9. Decorative Elements

- Gold gradient line divider: `h-px bg-gradient-to-r from-transparent via-gold-500/30 to-transparent`
- Section ornaments: never more than 1 decorative line per section
- Glow blobs: `bg-gold-500/5 rounded-full blur-3xl` — max 2 per card
- Heading ornament: optional flex row with gradient lines before/after text

---

## 10. Accessibility

- **Contrast**: all text must pass WCAG AA (4.5:1 for body, 3:1 for large text)
- **Focus**: visible focus ring on all interactive elements (`ring-2 ring-gold-500/40`)
- **Screen readers**: canvas is `aria-hidden="true"`, semantic HTML throughout
- **Reduced motion**: `@media (prefers-reduced-motion: reduce)` disables animations
- **Keyboard**: all links/buttons focusable, logical tab order
- **Touch targets**: minimum 44px for mobile interactive elements

---

## 11. Responsive Breakpoints

| Breakpoint | Width | Adjustments |
|------------|-------|-------------|
| Mobile | < 640px | Single column, reduced text, stacked CTAs |
| Tablet | 640-1024px | 2-column grids, moderate text |
| Desktop | > 1024px | Full layout, 3-column grids |

### Mobile-specific
- Hero text: `text-5xl` max
- Cards: full-width
- Nav: hamburger menu
- CTAs: stacked vertically

---

## 12. Component Rules

### Navigation
- Frosted glass pill on landing page
- Fixed position, z-50
- Logo: gold gradient square with Om symbol
- Active route: gold background tint
- Mobile: slide-down menu with backdrop

### Hero
- Full viewport height (`min-h-screen`)
- Centered content, max-w-5xl
- Trust badge above heading (pill, glass, icon + text)
- Heading: 2-line, gradient word + plain word
- Subtitle: 1-2 lines max
- CTAs: 2 buttons side by side (desktop) or stacked (mobile)
- Stats: grid below divider line
- Scroll indicator: subtle mouse icon at bottom

### Story Section
- Card grid: 2-3 columns
- Each card: icon (gradient bg) + title (serif) + description (sans)
- Quote block at bottom: serif blockquote with stats

### CTA Section
- Single centered card
- Badge + heading + description + button
- Decorative glow blobs

### Footer
- Minimal, single line
- Logo left, links/status right
- Border-top separator

---

## 13. Canvas Background Rules

The procedural background is AstroSage's most distinctive element. It must:

1. Fill the hero viewport (`position: fixed`)
2. Layer from back to front: sky → sun → rays → moon → clouds → far mountains → mid mountains → temple → chariot → near mountains → mist → particles
3. Use warm dawn palette (ivory → gold → amber)
4. Silhouette style for all figures (no detail rendering)
5. Blend seamlessly into page background at bottom
6. Never consume input events (`pointer-events: none`)
7. Respond to window resize
8. Cap DPR at 2 for performance
9. Respect `prefers-reduced-motion` (optional: reduce particle count)

---

## 14. Illustration Rules

- **Style**: Silhouettes only — dark shapes against atmospheric gradient background
- **Color**: Dark warm brown/charcoal silhouettes
- **No**: outlines, details, facial features, colors on figures
- **Respectful**: Deity figures are part of the environment, not decorations
- **Proportions**: Krishna taller than Arjuna, both proportional to chariot

---

## 15. File Organization

- `src/app/globals.css` — all CSS tokens, utilities, animations
- `src/components/landing/` — landing page components only
- `src/components/shared/` — reusable across pages
- `DESIGN_SYSTEM.md` — this document (source of truth)
