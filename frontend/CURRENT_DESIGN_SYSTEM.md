# AstroSage — Current Design System Extraction

*Extracted: 2026-07-22*

---

## Colors

### Surface Colors
| Token | Value | Usage |
|-------|-------|-------|
| `surface` | `#f8f6f2` | Page background (warm ivory) |
| `surface-elevated` | `#ffffff` | Cards, modals, elevated surfaces |
| `surface-overlay` | `rgba(255,255,255,0.85)` | Glass panels, overlays |

### Text Colors
| Token | Value | Usage |
|-------|-------|-------|
| `text-primary` | `#2c2418` | Headlines, body text (warm dark brown) |
| `text-secondary` | `#6b5d4f` | Descriptions, secondary content |
| `text-tertiary` | `#9a8b7a` | Captions, labels, placeholders |

### Gold Accent Scale
| Token | Value | Usage |
|-------|-------|-------|
| `gold-50` | `#fefcf5` | Tinted backgrounds |
| `gold-100` | `#fdf5e0` | Hover states |
| `gold-200` | `#fae8b8` | Light highlights |
| `gold-300` | `#f5d68a` | Medium highlights |
| `gold-400` | `#eec05a` | Active states, icons |
| `gold-500` | `#d4a030` | Primary accent, buttons |
| `gold-600` | `#b88820` | Hover accent, emphasis |
| `gold-700` | `#9a6e18` | Active accent, dark text |
| `gold-800` | `#7a5510` | Deep accent |
| `gold-900` | `#543a08` | Darkest accent |

### Purple/Sacred Scale (DEFINED BUT UNUSED)
| Token | Value | Status |
|-------|-------|--------|
| `astrosage-50` to `astrosage-900` | `#f5f0ff` to `#121050` | UNUSED |
| `sacred-50` to `sacred-900` | `#f8f6ff` to `#1f1248` | UNUSED |
| `deep-50` to `deep-900` | `#f2f4ff` to `#101866` | UNUSED |

### Semantic Colors
| Token | Value | Usage |
|-------|-------|-------|
| `success` | `#4a9e6a` | Quality gates, positive indicators |
| `warning` | `#d4a030` | Warnings (same as gold-500) |
| `error` | `#c45050` | Errors, low confidence |

### Border Colors
| Token | Value | Usage |
|-------|-------|-------|
| `border` | `rgba(60,45,30,0.08)` | Default dividers |
| `border-light` | `rgba(60,45,30,0.15)` | Emphasis borders |

---

## Typography

### Font Families
| Name | Font | Weights | Usage |
|------|------|---------|-------|
| `--font-inter` | Inter | 400-700 | Body, UI text |
| `--font-cormorant` | Cormorant Garamond | 300-700 | Headlines, display |

### Type Scale
| Level | Class | Size | Weight | Font | Line-height |
|-------|-------|------|--------|------|-------------|
| Hero | `text-5xl` to `text-7xl` | 48-72px | Bold | Serif | 1.06-1.1 |
| Section | `text-4xl` to `text-5xl` | 36-48px | Bold | Serif | 1.15 |
| Card | `text-xl` | 20px | Semibold | Serif | 1.3 |
| Body LG | `text-lg` | 18px | Normal | Sans | 1.6 |
| Body | `text-base` | 16px | Normal | Sans | 1.6 |
| Small | `text-sm` | 14px | Normal | Sans | 1.5 |
| Caption | `text-xs` | 12px | Medium | Sans | 1.4 |
| Micro | `text-[10px]` | 10px | Normal | Sans | 1.4 |

---

## Spacing

### Tailwind Scale (Base: 4px)
| Token | Value | Common Usage |
|-------|-------|-------------|
| `p-1` / `gap-1` | 4px | Tight gaps |
| `p-2` / `gap-2` | 8px | Icon gaps, small padding |
| `p-3` | 12px | Button padding |
| `p-4` | 16px | Card padding, input padding |
| `p-5` | 20px | Card internal spacing |
| `p-6` | 24px | Section gaps |
| `p-7` / `p-8` | 28-32px | Card large padding |
| `p-10` | 40px | Section padding |
| `p-12` | 48px | Major section padding |
| `p-16` | 64px | Hero CTA padding |
| `py-28` / `py-32` | 112-128px | Section vertical spacing |
| `pt-24` | 96px | Page top offset (nav) |
| `pt-32` | 128px | Hero top offset |

---

## Elevation & Glass

### Shadows (Custom)
```css
shadow-sm:  0 1px 3px rgba(60,45,30,0.04)
shadow-md:  0 4px 12px rgba(60,45,30,0.06)
shadow-lg:  0 8px 32px rgba(60,45,30,0.06)
```

### Glass Morphism Variants
| Class | Background | Blur | Border |
|-------|-----------|------|--------|
| `.glass` | `rgba(255,255,255,0.5)` | 20px | `rgba(60,45,30,0.08)` |
| `.glass-strong` | `rgba(255,255,255,0.75)` | 32px | `rgba(60,45,30,0.10)` |
| `.glass-warm` | `rgba(252,249,242,0.7)` | 24px | `rgba(212,160,48,0.12)` |

---

## Border Radius

| Element | Radius Class | Value |
|---------|-------------|-------|
| Buttons | `rounded-xl` | 12px |
| Cards | `rounded-2xl` | 16px |
| Nav pill | `rounded-2xl` | 16px |
| Badges | `rounded-full` | 9999px |
| Inputs | `rounded-xl` | 12px |
| Modals | `rounded-3xl` | 24px |

---

## Animation & Motion

### Keyframe Animations
| Name | Duration | Effect |
|------|----------|--------|
| `fadeIn` | 0.5s | Opacity 0→1, translateY 8px→0 |
| `fadeInUp` | 0.6s | Opacity 0→1, translateY 20px→0 |
| `slideInRight` | 0.4s | Opacity 0→1, translateX 20px→0 |
| `pulseGlow` | 2s loop | Box-shadow pulsing gold glow |
| `shimmer` | 2s loop | Background position sweep |
| `float` | 6s loop | translateY oscillation ±10px |

### Framer Motion Presets
| Name | Duration | Easing | Usage |
|------|----------|--------|-------|
| Hero entrance | 0.8-1.0s | easeOut | Staggered fade-in-up |
| Card entrance | 0.55s | easeOut | Scroll-triggered |
| Section entrance | 0.7s | easeOut | Scroll-triggered |
| Drawer slide | spring | damping:28, stiffness:280 | Evidence drawer |
| Sidebar toggle | 0.2s | easeInOut | Width animation |
| Message enter | 0.3s | easeOut | Chat messages |

### Stagger Classes
| Class | Delay |
|-------|-------|
| `.stagger-1` | 100ms |
| `.stagger-2` | 200ms |
| `.stagger-3` | 300ms |
| `.stagger-4` | 400ms |
| `.stagger-5` | 500ms |
| `.stagger-6` | 600ms |

---

## Layout

### Max Widths
| Context | Class | Value |
|---------|-------|-------|
| Content | `max-w-4xl` | 896px |
| Wide content | `max-w-6xl` | 1152px |
| Full width | `max-w-7xl` | 1280px |

### Responsive Breakpoints
| Name | Min Width | Strategy |
|------|-----------|----------|
| Default | 0px | Single column, stacked |
| `sm` | 640px | Minor adjustments |
| `md` | 768px | Two-column grids, horizontal CTAs |
| `lg` | 1024px | Full layout, three-column grids |
| `xl` | 1280px | Maximum width containers |

---

## Component Patterns

### Buttons
- `.btn-primary`: Gold gradient, white text, hover lift + glow
- `.btn-secondary`: Glass background, dark text, border
- CVA Button: 6 variants × 8 sizes (shadcn)

### Cards
- `.card-premium`: white, rounded-2xl, shadow, border, hover glow
- Glass cards: `.glass` or `.glass-strong` with rounded corners

### Forms
- Inputs: `bg-surface-elevated rounded-xl border border-border`
- Focus: `focus:ring-1 focus:ring-gold-500/30 focus:border-gold-500/30`

### Navigation
- Fixed, z-50, frosted glass pill
- Logo: gold gradient square + Om symbol
- Active: `bg-gold-500/10 text-gold-700`
- Mobile: slide-down with backdrop

---

## Iconography

- **Library**: Lucide React (lucide-react)
- **Size**: `h-3 w-3` (micro) to `h-7 w-7` (large)
- **Color**: `text-gold-400` for accent, `text-text-tertiary` for neutral
- **Usage**: Inline with text, standalone in buttons/cards

---

## Canvas Backgrounds

### Home Page: CinematicBackground
- Hero artwork image as base layer
- Canvas overlay: light rays, atmospheric particles, mist, vignette
- DPR capped at 2
- Respects prefers-reduced-motion

### Other Pages: StarField
- Star field with twinkling
- Constellation lines
- Floating particles (gold + purple)
- Floating lamps (diya-inspired)
- Sacred geometry rings
- Temple silhouette
- DPR capped at 2
- Pauses when not visible (IntersectionObserver)

---

*This document represents the EXTRACTED current state. The redesign will replace most of these patterns.*
