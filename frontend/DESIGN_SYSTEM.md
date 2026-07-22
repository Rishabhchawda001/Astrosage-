# AstroSage Design System v2.0

## Purpose

AstroSage's permanent visual constitution. Every UI decision must comply with this document.

---

## 1. Visual Philosophy

AstroSage is not software. It is a gateway to timeless knowledge. The interface must feel like entering a premium ancient library powered by modern engineering.

**Core emotions**: Trust · Calm · Wisdom · Timelessness · Reverence · Discovery

**Anti-patterns**: No neon. No gaming aesthetics. No heavy gradients. No clutter. No flashiness. No template feel. No generic SaaS.

---

## 2. Color System

### Surface Colors
| Token | Value | Usage |
|-------|-------|-------|
| `surface` | `#fefdfb` | Page background (warm ivory) |
| `surface-raised` | `#ffffff` | Cards, modals, elevated surfaces |
| `surface-overlay` | `rgba(255,255,255,0.92)` | Glass panels, overlays |
| `surface-sunken` | `#f5f3ef` | Recessed areas |

### Text Colors
| Token | Value | Usage |
|-------|-------|-------|
| `text-primary` | `#1a1612` | Headlines, body text |
| `text-secondary` | `#5c5347` | Descriptions, secondary content |
| `text-tertiary` | `#9a9083` | Captions, labels, placeholders |

### Gold Accent (Subtle)
| Token | Value | Usage |
|-------|-------|-------|
| `gold-50` to `gold-900` | Warm gold scale | Accent, buttons, emphasis |
| `accent` | `#d4a84a` | Primary accent |
| `accent-subtle` | `rgba(212,168,74,0.06)` | Subtle accent backgrounds |
| `accent-muted` | `rgba(212,168,74,0.12)` | Muted accent backgrounds |

### Borders
| Token | Value | Usage |
|-------|-------|-------|
| `border` | `rgba(26,22,18,0.06)` | Default dividers |
| `border-subtle` | `rgba(26,22,18,0.04)` | Very subtle dividers |
| `border-strong` | `rgba(26,22,18,0.10)` | Emphasis borders |
| `border-accent` | `rgba(212,168,74,0.15)` | Gold accent borders |

---

## 3. Typography

### Font Families
- **Display / Headlines**: Cormorant Garamond (serif, elegant, museum-quality)
- **Body / UI**: Inter (sans-serif, clean, excellent readability)

### Type Scale
| Level | Size | Weight | Font | Usage |
|-------|------|--------|------|-------|
| Display | `text-5xl` to `text-7xl` (48-72px) | Bold | Serif | Hero headings |
| Section | `text-4xl` to `text-5xl` (36-48px) | Bold | Serif | Section titles |
| Card | `text-xl` (20px) | Semibold | Serif | Card titles |
| Body LG | `text-lg` (18px) | Normal | Sans | Lead paragraphs |
| Body | `text-base` (16px) | Normal | Sans | Body text |
| Small | `text-sm` (14px) | Normal | Sans | UI text |
| Caption | `text-xs` (12px) | Medium | Sans | Captions |
| Micro | `text-[11px]` | Normal | Sans | Fine print |
| Label | `text-[11px] uppercase tracking-wider` | Medium | Sans | Section labels |

### Rules
- Headlines always use serif font
- Body text never exceeds 680px width
- Gold gradient text only for key emphasis words (max 1-2 per heading)
- Letter spacing: tight on headings, normal on body

---

## 4. Spacing

Base unit: 4px (Tailwind default)

| Token | Value | Usage |
|-------|-------|-------|
| `p-1` / `gap-1` | 4px | Tight gaps |
| `p-2` / `gap-2` | 8px | Icon gaps, small padding |
| `p-3` | 12px | Button padding, card internal |
| `p-4` | 16px | Card padding, input padding |
| `p-5` | 20px | Card internal spacing |
| `p-6` | 24px | Section gaps |
| `p-7` / `p-8` | 28-32px | Card large padding |
| `p-10` | 40px | Section padding |
| `p-12` | 48px | Major section padding |
| `p-16` | 64px | Hero CTA padding |
| `py-28` / `py-32` | 112-128px | Section vertical spacing |
| `pt-24` | 96px | Page top offset (nav) |

---

## 5. Elevation & Shadows

### Shadow Scale
```css
shadow-xs:  0 1px 2px rgba(26,22,18,0.03)
shadow-sm:  0 1px 3px rgba(26,22,18,0.04), 0 1px 2px rgba(26,22,18,0.02)
shadow-md:  0 4px 12px rgba(26,22,18,0.04), 0 2px 4px rgba(26,22,18,0.02)
shadow-lg:  0 8px 24px rgba(26,22,18,0.05), 0 4px 8px rgba(26,22,18,0.02)
shadow-xl:  0 16px 48px rgba(26,22,18,0.06), 0 8px 16px rgba(26,22,18,0.03)
shadow-2xl: 0 24px 64px rgba(26,22,18,0.08), 0 12px 24px rgba(26,22,18,0.04)
shadow-glow: 0 0 40px rgba(212,168,74,0.08)
```

### Glass Morphism
| Class | Background | Blur | Border |
|-------|-----------|------|--------|
| `.glass` | `rgba(255,255,255,0.55)` | 20px | `border` |
| `.glass-strong` | `rgba(255,255,255,0.78)` | 32px | `border-strong` |
| `.glass-subtle` | `rgba(255,255,255,0.35)` | 12px | `border-subtle` |

---

## 6. Border Radius

| Element | Radius | Value |
|---------|--------|-------|
| Buttons | `rounded-xl` | 18px |
| Cards | `rounded-2xl` | 24px |
| Nav pill | `rounded-2xl` | 24px |
| Badges | `rounded-full` | 9999px |
| Inputs | `rounded-xl` | 18px |
| Modals | `rounded-3xl` | 32px |

---

## 7. Card System

- `.card`: Base card — white, rounded-2xl, border, shadow-sm, hover shadow-md
- `.card-elevated`: Higher elevation — white, rounded-2xl, border, shadow-lg
- `.card-premium`: Premium card — white, rounded-2xl, border, shadow-md, hover glow + lift

---

## 8. Button System

### Primary (`.btn-primary`)
- Gold gradient background
- White text, semibold
- Rounded-xl, generous padding
- Hover: brighter gradient, stronger shadow, lift

### Secondary (`.btn-secondary`)
- White surface background
- Dark text, medium weight
- Border, rounded-xl
- Hover: warm-50 background, stronger border

---

## 9. Motion

### Duration Tokens
| Token | Value | Usage |
|-------|-------|-------|
| `duration-fast` | 120ms | Micro interactions |
| `duration-normal` | 200ms | Standard transitions |
| `duration-slow` | 350ms | Page transitions |
| `duration-slower` | 500ms | Complex animations |
| `duration-slowest` | 700ms | Cinematic entrances |

### Easing
| Token | Value | Usage |
|-------|-------|-------|
| `ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Most transitions |
| `ease-in-out` | `cubic-bezier(0.65, 0, 0.35, 1)` | Bidirectional |
| `ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Bouncy entrances |

### Framer Motion Presets
| Name | Duration | Easing | Usage |
|------|----------|--------|-------|
| Hero entrance | 0.8-1.0s | easeOut | Staggered fade-in-up |
| Card entrance | 0.5s | easeOut | Scroll-triggered |
| Section entrance | 0.6s | easeOut | Scroll-triggered |
| Drawer slide | spring | damping:30, stiffness:300 | Evidence drawer |
| Sidebar toggle | 0.2s | easeOut | Width animation |
| Message enter | 0.3s | easeOut | Chat messages |

### Rules
- Entrance animations: fade-in-up (6-16px translation)
- Scroll reveals: `useInView` with `once: true`
- Canvas: continuous, 60fps, never blocks interaction
- `prefers-reduced-motion`: disable all animations except canvas background

---

## 10. Canvas Backgrounds

### Home Page: CinematicBackground
- Sacred geometry (concentric circles, lotus petal patterns)
- Flowing river geometry (sine waves)
- Light rays from above
- Mountain silhouettes
- Atmospheric particles (dust, petals, pollen)
- Mist gradient at bottom
- Soft vignette
- DPR capped at 2

### Other Pages: StarField
- Sparse floating gold particles
- Warm radial gradient
- Pauses when not visible (IntersectionObserver)
- DPR capped at 2

---

## 11. Accessibility

- **Contrast**: all text passes WCAG AA (4.5:1 body, 3:1 large)
- **Focus**: visible focus ring on all interactive elements
- **Screen readers**: canvas is `aria-hidden="true"`, semantic HTML
- **Reduced motion**: `@media (prefers-reduced-motion: reduce)` disables animations
- **Keyboard**: all links/buttons focusable, logical tab order
- **Touch targets**: minimum 44px for mobile interactive elements

---

## 12. Responsive Breakpoints

| Name | Min Width | Strategy |
|------|-----------|----------|
| Mobile | 0px | Single column, stacked |
| `sm` | 640px | Minor adjustments |
| `md` | 768px | Two-column, horizontal CTAs |
| `lg` | 1024px | Full layout, three-column |
| `xl` | 1280px | Maximum width containers |

---

*Generated: 2026-07-22*
*Version: 2.0*
