# AstroSage Frontend Audit — Complete Analysis

## 1. Architecture Overview

| Aspect | Status |
|--------|--------|
| Framework | Next.js 16 (App Router) |
| React | 19.2.4 |
| Styling | Tailwind CSS v4 + globals.css (411 lines) |
| State Management | Zustand (5 stores: Auth, Chat, Search, UI, Bookmarks) |
| Animation | Framer Motion 12 + CSS keyframes |
| UI Primitives | @base-ui/react + Radix-inspired patterns |
| Forms | Native controlled components (no form library in frontend) |
| HTTP | Fetch API with custom wrapper (no axios) |
| Build | Vite via Next.js, standalone output |
| Package Manager | npm (package-lock.json) |
| Linting | ESLint (eslint-config-next) |
| Type Checking | TypeScript 5 |

---

## 2. Routing (Next.js App Router)

| Route | File | Description |
|-------|------|-------------|
| `/` | `app/page.tsx` | Landing page — hero, story, CTA, footer |
| `/chat` | `app/chat/page.tsx` | AI chat interface with sidebar, search mode, streaming |
| `/search` | `app/search/page.tsx` | Knowledge base search (entities, verses) |
| `/explore` | `app/explore/page.tsx` | Knowledge graph explorer with force-directed visualization |
| `/login` | `app/login/page.tsx` | Authentication form |
| `/register` | `app/register/page.tsx` | Registration form |

### Routing Issues
- No route protection/middleware — all pages are client-side only (`"use client"`)
- No layout nesting — each page includes `<Navigation />` independently
- No loading states per route (except global `loading.tsx`)
- No dynamic routes for entity detail views

---

## 3. Component Hierarchy

```
app/layout.tsx
├── fonts: Inter + Cormorant_Garamond
├── Toaster (sonner)
└── {children}
    ├── page.tsx (Home)
    │   ├── CinematicBackground (Canvas 2D)
    │   ├── Navigation
    │   ├── HeroSection
    │   ├── StorySection (7 story cards)
    │   ├── CTASection
    │   └── Footer (inline)
    ├── chat/page.tsx
    │   ├── StarField (Canvas 2D)
    │   ├── Navigation
    │   ├── ConversationSidebar
    │   ├── MessageBubble (multiple)
    │   ├── ChatInput
    │   └── EvidenceDrawer
    ├── search/page.tsx
    │   ├── StarField
    │   ├── Navigation
    │   └── EvidenceDrawer
    ├── explore/page.tsx
    │   ├── StarField
    │   ├── Navigation
    │   └── GraphPreview (Canvas 2D force-directed)
    ├── login/page.tsx
    │   ├── StarField
    │   └── Navigation
    └── register/page.tsx
        ├── StarField
        └── Navigation
```

---

## 4. Component Inventory

### Landing (`components/landing/`)
| Component | Lines | Description |
|-----------|-------|-------------|
| `CinematicBackground.tsx` | ~280 | Canvas 2D with artwork image, light rays, particles, mist, vignette |
| `HeroSection.tsx` | ~100 | Hero with trust badge, heading, CTA buttons, stats |
| `StorySection.tsx` | ~130 | 7 feature cards with scroll-triggered animation |
| `CTASection.tsx` | ~80 | Final CTA card with glow blobs |
| `StarField.tsx` | ~390 | Canvas 2D starfield with constellations, floating lamps, temple silhouette, sacred geometry |

### Shared (`components/shared/`)
| Component | Lines | Description |
|-----------|-------|-------------|
| `Navigation.tsx` | ~160 | Fixed frosted glass nav with mobile menu |
| `EvidenceDrawer.tsx` | ~230 | Slide-in drawer for scripture evidence details |
| `GraphPreview.tsx` | ~320 | Interactive force-directed graph canvas |

### Chat (`components/chat/`)
| Component | Lines | Description |
|-----------|-------|-------------|
| `ChatInput.tsx` | ~90 | Auto-resizing textarea with send/stop buttons |
| `MessageBubble.tsx` | ~280 | Chat message with markdown, sources, bookmarks |
| `ConversationSidebar.tsx` | ~220 | Sidebar with pinned/recent conversations, search |

### UI Primitives (`components/ui/`)
| Component | Description |
|-----------|-------------|
| `button.tsx` | CVA-based button with 6 variants, 8 sizes |
| `sonner.tsx` | Toast wrapper with icons |

---

## 5. Design System Analysis

### Current Theme (globals.css — 411 lines)
**Color Palette:**
- 5 custom color scales: astrosage (purple), gold, sacred (purple), deep (blue), surface
- 3 surface tokens: surface (#f8f6f2), surface-elevated (#ffffff), surface-overlay
- 3 text tokens: primary (#2c2418), secondary (#6b5d4f), tertiary (#9a8b7a)
- Accent: gold-500 (#d4a030)
- Semantic: success (#4a9e6a), error (#c45050), warning (#d4a030)
- Border: rgba(60,45,30,0.08) and rgba(60,45,30,0.15)

**Typography:**
- Display: Cormorant Garamond (serif, weights 300-700)
- Body: Inter (sans-serif)
- Scale from text-xs to text-7xl via Tailwind
- `prose-custom` class for markdown content

**Custom CSS:**
- 6 keyframe animations (fadeIn, fadeInUp, slideInRight, pulseGlow, shimmer, float)
- 6 stagger delay classes
- 3 glass morphism variants (glass, glass-strong, glass-warm)
- Gradient text utilities (gradient-gold, gradient-warm)
- Button styles (.btn-primary, .btn-secondary)
- Skeleton loading, typing indicator, citation card styles
- Focus-visible states for accessibility
- Custom scrollbar styling
- Prose/typography styles for markdown content

### Design Strengths ✅
1. Warm, premium color palette (ivory surfaces, gold accents)
2. Good typography pairing (serif headlines + sans body)
3. Consistent glass morphism language
4. Proper reduced-motion support
5. WCAG AA focus states
6. Clean component architecture
7. Well-structured design tokens

### Design Issues ❌
1. **Purple color scales unused** — astrosage-*, sacred-*, deep-* scales are defined but never used in components
2. **Inconsistent glass usage** — some pages use glass, others use bg-white directly
3. **No consistent card component** — cards are styled inline each time
4. **No consistent spacing tokens** — mixing arbitrary values and Tailwind defaults
5. **Large globals.css** — 411 lines mixing tokens, utilities, components, animations
6. **No dark mode** — no theme provider or dark tokens
7. **No design token exports** — tokens only in CSS, not accessible from JS

---

## 6. Animation Analysis

### Current Animation Stack
1. **CSS Keyframes** (globals.css): fadeIn, fadeInUp, slideInRight, pulseGlow, shimmer, float
2. **Framer Motion**: Used in HeroSection, StorySection, CTASection, MessageBubble, ConversationSidebar, EvidenceDrawer, Chat page
3. **Canvas 2D**: CinematicBackground (hero), StarField (non-hero pages), GraphPreview (explore)

### Animation Issues
- **Two competing canvas backgrounds** — CinematicBackground on home, StarField on other pages
- **StarField is heavy** — stars, constellations, particles, lamps, sacred geometry, temple silhouette — all in one canvas
- **No page transitions** — hard cuts between routes
- **No loading skeletons** on data-dependent pages
- **Stagger animations** use CSS classes but inconsistently applied
- **Scroll animations** only on landing page (useInView)

---

## 7. State Management

### Zustand Stores
| Store | Fields | Persistence |
|-------|--------|-------------|
| `useAuthStore` | isAuthenticated, username | localStorage |
| `useChatStore` | messages, streaming, conversations, pinned, search | localStorage (pinned only) |
| `useSearchStore` | query, results, searching | None |
| `useUIStore` | sidebar, evidenceDrawer, selectedEvidence | None |
| `useBookmarkStore` | bookmarks | localStorage |

### State Issues
- **No global loading/error states** — each page manages its own
- **No route-level state isolation** — chat state persists across navigation
- **Auth token refresh** is manual in api.ts, not reactive
- **Bookmark state** uses `useBookmarkStore.getState()` in JSX (anti-pattern in React)

---

## 8. Performance Analysis

### Current Performance Characteristics
- **3 Canvas elements** potentially running simultaneously
- **No code splitting** beyond Next.js automatic chunks
- **No lazy loading** of route components
- **No image optimization** — single hero artwork loaded as raw Image()
- **Heavy StarField** on every non-landing page (chat, search, explore, login, register)
- **No virtual list** for search results or conversation list
- **Client-side only** — no SSR/SSG benefits utilized (all pages are "use client")

### Bundle Concerns
- framer-motion is heavy (~40KB gzipped)
- recharts not used in frontend (only in backend's workspace)
- @tanstack/react-query imported but not used in any component
- Multiple Lucide icons imported per page

---

## 9. Accessibility

### Strengths
- Focus-visible states on buttons and links
- aria-hidden on canvas elements
- Semantic HTML (main, nav, section, footer)
- aria-label on interactive elements
- Keyboard navigation support

### Issues
- No skip-to-content link
- No aria-live regions for streaming messages
- Mobile menu lacks focus trap
- Search results not announced to screen readers
- Color contrast may be insufficient on gold-on-white combinations
- No prefers-reduced-motion on StarField/CinematicBackground (only partial)

---

## 10. Responsive Design

### Breakpoints (Tailwind defaults)
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px

### Responsive Issues
- Chat page has complex responsive logic (sidebar collapse, search mode)
- StarField canvas doesn't optimize for mobile (full particle count)
- Knowledge graph on mobile may be unusable (small canvas)
- Some text sizes not responsive (fixed text-xs in many places)

---

## 11. File Organization

```
frontend/src/
├── app/
│   ├── layout.tsx          (root layout, fonts, metadata)
│   ├── page.tsx            (landing)
│   ├── globals.css         (411 lines — all tokens + utilities)
│   ├── loading.tsx
│   ├── error.tsx
│   ├── not-found.tsx
│   ├── robots.ts
│   ├── sitemap.ts
│   ├── chat/page.tsx       (547 lines — largest file)
│   ├── search/page.tsx     (297 lines)
│   ├── explore/page.tsx    (297 lines)
│   ├── login/page.tsx      (150 lines)
│   └── register/page.tsx   (150 lines)
├── components/
│   ├── landing/            (4 components)
│   ├── shared/             (3 components)
│   ├── chat/               (3 components)
│   └── ui/                 (2 components)
├── lib/
│   ├── api.ts              (300+ lines — all API calls)
│   ├── store.ts            (180 lines — all Zustand stores)
│   └── utils.ts            (5 lines — cn utility)
├── types/
│   └── api.ts              (170 lines — all TypeScript types)
└── main.tsx                (not used — Next.js uses layout.tsx)
```

---

## 12. Summary of Key Findings

### What Works Well
1. Clean component decomposition
2. Good use of custom hooks patterns
3. Warm, premium color palette foundation
4. Proper TypeScript typing throughout
5. Canvas-based backgrounds are distinctive
6. Glass morphism design language is cohesive
7. Evidence/citation system is well-designed

### Critical Issues to Address
1. **Unused color scales** (purple/blue defined but never used)
2. **No dark mode** support
3. **Heavy canvas animations** on every page
4. **No page transitions**
5. **No loading skeletons**
6. **Inconsistent component patterns**
7. **Missing accessibility features**
8. **Client-only rendering** (no SSR benefits)
9. **Large monolithic page files** (chat page is 547 lines)
10. **No consistent spacing/radius/motion tokens** exported

---

*Generated: 2026-07-22*
*Scope: AstroSage Frontend (Next.js 16 + React 19 + Tailwind v4)*
