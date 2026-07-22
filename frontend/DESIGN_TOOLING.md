# AstroSage Design Tooling — Selection & Architecture

## Decision: Custom Design Framework

The "OpenDesign" npm packages (`opendesign`, `@opensig/opendesign`, `@opendesign/react`) are either
Vue-based, unmaintained (last publish 2023), or unrelated file format tools. None provide the
desired capabilities: design extraction, design system generation, motion system, design tokens,
component architecture, UI critique, or artifact generation.

**Decision**: Build a custom, best-in-class design framework using proven open-source tools.

---

## Selected Tooling Stack

### 1. Design Tokens — Style Dictionary (via Tailwind v4 @theme)
- **What**: Custom Tailwind v4 theme system with CSS custom properties
- **Why**: Native to the stack, zero runtime cost, supports all CSS platforms
- **Usage**: Color, spacing, typography, elevation, radius, motion tokens in `globals.css`

### 2. Component Architecture — shadcn/ui + CVA
- **What**: Class Variance Authority for type-safe component variants
- **Why**: Already installed, proven at scale, maximum flexibility
- **Usage**: All UI primitives (Button, Input, Card, Badge, etc.)

### 3. Motion System — Framer Motion 12
- **What**: Production-grade React animation library
- **Why**: Already installed, GPU-accelerated, gesture support, layout animations
- **Usage**: Page transitions, micro-interactions, scroll animations, hover states

### 4. Canvas Rendering — Custom Canvas 2D / WebGL
- **What**: Handcrafted procedural backgrounds
- **Why**: Full control over performance, aesthetics, and interaction
- **Usage**: Hero background, ambient effects, knowledge graph visualization

### 5. Design Documentation — Markdown-based Design System
- **What**: Living design documentation in the repository
- **Why**: Version-controlled, always accurate, directly beside code
- **Usage**: DESIGN_SYSTEM.md, COMPONENT_GUIDE.md, MOTION_GUIDE.md

### 6. Visual Language — Custom AstroSage Identity
- **What**: Bespoke design language for Sanātana Dharma knowledge platform
- **Why**: No off-the-shelf framework captures this domain's essence
- **Usage**: Color palette, typography, iconography, patterns, motion principles

---

## Why Not Alternatives

| Alternative | Reason for Rejection |
|-------------|---------------------|
| Material UI (MUI) | Too generic, not premium enough, heavy bundle |
| Chakra UI | Template-like feel, not custom enough |
| Ant Design | Enterprise/Chinese-market aesthetic, wrong tone |
| Radix Themes | Good primitives but limited design language |
| OpenDesign npm | Unmaintained, Vue-only, or unrelated |
| Headless UI | Too minimal, no design system included |
| Park UI | Too new, limited ecosystem |

---

## Implementation Plan

### Phase 1: Design Token System
- Define all tokens in Tailwind v4 `@theme` block
- Create semantic token layers (base → semantic → component)
- Export tokens for runtime use via CSS custom properties

### Phase 2: Component Library
- Build 12 core primitives with CVA variants
- Ensure type safety, accessibility, and consistency
- Document each component's usage and variants

### Phase 3: Motion System
- Define motion tokens (duration, easing, spring configs)
- Create reusable animation presets
- Implement page transitions and scroll animations

### Phase 4: Canvas System
- Design GPU-accelerated ambient backgrounds
- Implement 60fps with low CPU usage
- Support prefers-reduced-motion

### Phase 5: Documentation
- Design System documentation
- Component API documentation
- Motion guidelines
- Theme customization guide

---

*Generated: 2026-07-22*
