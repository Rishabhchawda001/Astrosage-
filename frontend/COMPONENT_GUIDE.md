# AstroSage Component Guide v2.0

## Component Architecture

```
components/
├── landing/          Landing page specific
│   ├── CinematicBackground.tsx   GPU-accelerated hero canvas
│   ├── HeroSection.tsx           Hero with staggered entrance
│   ├── StorySection.tsx          Feature cards with scroll reveal
│   ├── CTASection.tsx            Final call-to-action
│   └── StarField.tsx             Lightweight ambient canvas
├── shared/           Cross-page components
│   ├── Navigation.tsx            Fixed frosted glass nav
│   ├── EvidenceDrawer.tsx        Scripture evidence slide-in
│   └── GraphPreview.tsx          Force-directed graph canvas
├── chat/             Chat interface
│   ├── ChatInput.tsx             Auto-resizing textarea
│   ├── MessageBubble.tsx         Chat message with markdown
│   └── ConversationSidebar.tsx   Sidebar with conversations
└── ui/               Primitives
    └── button.tsx                CVA-based button (6 variants)
```

---

## Component Reference

### Navigation
- Fixed position, z-50
- Frosted glass pill on landing, solid glass on inner pages
- Logo: gold gradient square + Om symbol
- Desktop: horizontal links + CTA button
- Mobile: hamburger → slide-down menu
- Active route: accent-subtle background

### HeroSection
- Full viewport height
- Staggered entrance animation (0.1s delay between elements)
- Trust badge (pill, glass, icon + text)
- 2-line heading: gradient word + plain word
- 2 CTA buttons (primary + secondary)
- Stats strip below gold divider

### StorySection
- 7 feature cards in responsive grid
- Each card: icon (gold gradient bg) + title (serif) + description (sans)
- Scroll-triggered entrance (useInView, once)
- First card spans full width on desktop

### CTASection
- Single centered elevated card
- Badge + heading + description + button
- Decorative gold glow blobs (subtle)

### ChatInput
- Auto-resizing textarea (max 180px)
- Send button (gold) / Stop button (red)
- Helper text below input

### MessageBubble
- User: warm-100 background, right-aligned
- Assistant: white card with border, left-aligned
- Avatar: 7px circle, gold gradient for assistant
- Actions: copy, source count, bookmark
- Expandable source cards

### ConversationSidebar
- 280px width, collapsible
- Pinned section + Recent section
- Search input
- New Chat button (gold)
- Mobile: full-width overlay

### EvidenceDrawer
- Right slide-in (spring animation)
- Mobile: bottom sheet
- Trust indicator, scripture reference
- Relevance score bar
- Bookmarked sources list
- Provenance metadata

### GraphPreview
- Force-directed physics simulation
- Pan/zoom with mouse/touch
- Node hover highlighting
- Color-coded by entity type
- Zoom controls overlay

---

## Usage Patterns

### Adding a new page
1. Create `src/app/[name]/page.tsx`
2. Add `"use client"` if using state/interactions
3. Include `<StarField />` and `<Navigation />`
4. Use motion.div for entrance animations
5. Use card classes for content containers

### Adding a new component
1. Determine category (landing/shared/chat/ui)
2. Create file in appropriate directory
3. Use `"use client"` for interactive components
4. Follow existing naming conventions
5. Use design tokens from globals.css

### Animation pattern
```tsx
import { motion } from "framer-motion";

<motion.div
  initial={{ opacity: 0, y: 12 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.6, ease: "easeOut" }}
>
  Content
</motion.div>
```

### Scroll reveal pattern
```tsx
import { useRef } from "react";
import { motion, useInView } from "framer-motion";

const ref = useRef(null);
const inView = useInView(ref, { once: true, margin: "-50px" });

<motion.div
  ref={ref}
  initial={{ opacity: 0, y: 20 }}
  animate={inView ? { opacity: 1, y: 0 } : {}}
  transition={{ duration: 0.5, ease: "easeOut" }}
>
  Content
</motion.div>
```

---

*Generated: 2026-07-22*
