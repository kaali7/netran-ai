---
name: Serene Learning
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#49454d'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#7a757e'
  outline-variant: '#cbc4ce'
  surface-tint: '#65597b'
  primary: '#65597b'
  on-primary: '#ffffff'
  primary-container: '#e6d6ff'
  on-primary-container: '#675b7e'
  inverse-primary: '#cfc0e8'
  secondary: '#426651'
  on-secondary: '#ffffff'
  secondary-container: '#c3ecd2'
  on-secondary-container: '#486c57'
  tertiary: '#6d5a59'
  on-tertiary: '#ffffff'
  tertiary-container: '#f1d7d5'
  on-tertiary-container: '#6f5c5b'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ebddff'
  primary-fixed-dim: '#cfc0e8'
  on-primary-fixed: '#201634'
  on-primary-fixed-variant: '#4d4162'
  secondary-fixed: '#c3ecd2'
  secondary-fixed-dim: '#a8d0b6'
  on-secondary-fixed: '#002112'
  on-secondary-fixed-variant: '#2a4e3a'
  tertiary-fixed: '#f6dddb'
  tertiary-fixed-dim: '#d9c1bf'
  on-tertiary-fixed: '#261817'
  on-tertiary-fixed-variant: '#544342'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  headline-xl:
    fontFamily: Manrope
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Manrope
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-md:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Manrope
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Manrope
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  stats-number:
    fontFamily: Manrope
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 40px
  container-max: 1440px
  gutter: 20px
---

## Brand & Style

The brand personality is empathetic, calm, and intellectually stimulating. As a healthcare learning platform, it must balance clinical precision with an approachable, human-centric interface. The target audience includes medical students and professionals who often operate in high-stress environments; therefore, the UI serves as a "digital sanctuary"—reducing cognitive load through soft visuals and clear hierarchy.

The design style is **Modern Glassmorphism**. It utilizes translucent layers, subtle background blurs, and organic shapes to create a sense of breathability. By mixing clean minimalism with tactile, "frosted" elements, the system achieves a professional yet inviting aesthetic that feels cutting-edge and trustworthy.

## Colors

The palette is rooted in restorative hues. 
- **Primary (Lavender):** Used for active learning states, creative modules (e.g., Pharmacology), and primary calls to action.
- **Secondary (Mint Green):** Signifies completion, health, and positive progression.
- **Tertiary (Soft Peach/Yellow):** Used for alerts, tasks, or temporal events to provide gentle contrast without causing alarm.
- **Neutrals:** A range of cool grays and off-whites form the foundation, ensuring the interface remains lightweight.

Backgrounds should use very light tints of the primary/secondary colors to differentiate sections (e.g., a 5% mint tint for the "Completed" stats card).

## Typography

This design system uses **Manrope** for its modern, geometric construction that maintains high legibility in technical contexts. 

- **Headlines:** Use a bold weight with tighter letter spacing to create a strong visual anchor.
- **Body:** Standardized at 16px for optimal readability of medical descriptions.
- **Stats:** Large, prominent weights are used for progress tracking (e.g., "26 Total").
- **Contrast:** High-level headings use the `text_main` color, while secondary descriptions use a 60% opacity to establish clear information hierarchy.

## Layout & Spacing

The system employs a **Fluid Card-Based Grid**. 
- **Desktop:** A 12-column grid with generous 40px external margins. Content is grouped into "Panes" (Left Sidebar, Main Content, Right Activity Feed).
- **Mobile:** Single column with 16px side margins. The navigation moves to a bottom "dock" style to maintain thumb-reachability.
- **Rhythm:** An 8px linear scale governs all padding and margins. Use `md (24px)` for internal card padding and `lg (40px)` for section separation to maintain the "airy" feel.

## Elevation & Depth

Depth is achieved through a "Layered Glass" approach rather than traditional heavy shadows.
- **Level 1 (Base):** Subtle light gray/white background.
- **Level 2 (Cards):** White surfaces with a very soft, diffused shadow (`0px 10px 30px rgba(0,0,0,0.03)`).
- **Level 3 (Interactive/Floating):** Use a backdrop-filter blur (12px-20px) with 80% opacity fills. This is reserved for the bottom navigation dock and "Active" lesson cards.
- **Depth Cues:** Active items (like the "Pharmacology" card) should appear to "lift" using a slightly more pronounced shadow and a subtle scale-up (1.02x).

## Shapes

The shape language is defined by "Squircle" influences—very soft, friendly corners that avoid the clinical coldness of sharp edges.
- **Default (Cards/Inputs):** 16px (1rem).
- **Large (Containers/Main Wrappers):** 24px (1.5rem).
- **Buttons/Chips:** Fully rounded (Pill-shaped) to distinguish them as interactive elements.
- **Icon Enclosures:** Circular or 12px rounded squares.

## Components

- **Buttons:** Primary buttons use the Pill-shape with a subtle gradient or solid color. Secondary buttons use a "Ghost" style with a 1px border or a soft tinted background.
- **Chips (Status Labels):** Use low-saturation background tints (e.g., Mint for "Completed") with dark text. Include a small emoji or icon for quick visual scanning.
- **Cards:** The primary container. Must include a `border: 1px solid rgba(255,255,255,0.5)` to enhance the glass effect on tinted backgrounds.
- **Input Fields:** Search bars should be highly rounded (pill) with a light gray fill (`#F3F4F6`) and centered text/icons to maintain the minimalist aesthetic.
- **Progress Indicators:** Use thin, dotted lines to connect related learning modules, creating a "Path" metaphor.
- **The Dock:** A floating navigation bar at the bottom center, using glassmorphism (blur) and circular icon buttons.