# AstroSage Theme Guide v2.0

## Theme Architecture

AstroSage uses a single warm theme with CSS custom properties defined in the Tailwind v4 `@theme` block.

---

## Color Tokens

### How to Use

```tsx
// In JSX — Tailwind classes
<div className="bg-surface text-text-primary border border-border">

// In CSS — custom properties
background: var(--color-surface);
color: var(--color-text-primary);
```

### Surface Colors
| Class | Variable | Value |
|-------|----------|-------|
| `bg-surface` | `--color-surface` | `#fefdfb` |
| `bg-surface-raised` | `--color-surface-raised` | `#ffffff` |
| `bg-surface-sunken` | `--color-surface-sunken` | `#f5f3ef` |

### Text Colors
| Class | Variable | Value |
|-------|----------|-------|
| `text-text-primary` | `--color-text-primary` | `#1a1612` |
| `text-text-secondary` | `--color-text-secondary` | `#5c5347` |
| `text-text-tertiary` | `--color-text-tertiary` | `#9a9083` |

### Gold Scale
| Class | Variable | Value |
|-------|----------|-------|
| `text-gold-500` | `--color-gold-500` | `#d4a84a` |
| `bg-gold-500` | `--color-gold-500` | `#d4a84a` |
| `text-gold-600` | `--color-gold-600` | `#b8903a` |
| `text-gold-700` | `--color-gold-700` | `#96732e` |
| `bg-accent-subtle` | `--color-accent-subtle` | `rgba(212,168,74,0.06)` |

### Border Colors
| Class | Variable | Value |
|-------|----------|-------|
| `border-border` | `--color-border` | `rgba(26,22,18,0.06)` |
| `border-border-subtle` | `--color-border-subtle` | `rgba(26,22,18,0.04)` |
| `border-border-strong` | `--color-border-strong` | `rgba(26,22,18,0.10)` |
| `border-border-accent` | `--color-border-accent` | `rgba(212,168,74,0.15)` |

### Status Colors
| Class | Variable | Value |
|-------|----------|-------|
| `bg-success` | `--color-success` | `#3d8b5a` |
| `text-error` | `--color-error` | `#b84040` |
| `text-warning` | `--color-warning` | `#c49a2a` |

---

## Typography Tokens

### Font Families
| Class | Variable | Font |
|-------|----------|------|
| `font-sans` | `--font-sans` | Inter, system-ui |
| `font-serif` | `--font-serif` | Cormorant Garamond, Georgia |

### Usage
```tsx
<h1 className="font-serif text-4xl font-bold">Serif Heading</h1>
<p className="font-sans text-base">Sans Body Text</p>
```

---

## Shadow Tokens

```tsx
<div className="shadow-sm">  {/* Subtle */}
<div className="shadow-md">  {/* Default */}
<div className="shadow-lg">  {/* Elevated */}
<div className="shadow-xl">  {/* High */}
<div className="shadow-2xl"> {/* Maximum */}
```

---

## Radius Tokens

```tsx
<button className="rounded-xl">Button</button>    {/* 18px */}
<div className="rounded-2xl">Card</div>           {/* 24px */}
<div className="rounded-3xl">Modal</div>          {/* 32px */}
<span className="rounded-full">Badge</span>       {/* 9999px */}
```

---

## Adding New Tokens

1. Add to `@theme` block in `globals.css`
2. Use Tailwind convention: `--color-*`, `--font-*`, `--radius-*`, `--shadow-*`
3. Update DESIGN_SYSTEM.md
4. Test contrast ratios (WCAG AA minimum)

---

## Theme Customization

The current theme is a single warm theme. To add dark mode in the future:

1. Add `dark:` prefixed tokens
2. Wrap in ThemeProvider
3. Add toggle component
4. Update all components with dark variants

---

*Generated: 2026-07-22*
