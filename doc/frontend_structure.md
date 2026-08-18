# Netran AI — Frontend Architecture & Structure Specification

This document details the architecture, design tokens, component hierarchy, directory layout, and API integration contracts for the **Netran AI** web frontend client.

---

## 🎨 1. Design Tokens & Visual Architecture (from `DESIGN.md`)

* **Theme Name**: Serene Learning (Modern Glassmorphism)
* **Design Personality**: Empathetic, calm, intellectually stimulating digital sanctuary.
* **Typography**: **Manrope** (Google Fonts)
* **Corner Radius**: 
  - Cards / Containers: `16px` (1rem)
  - Modals / Large Wrappers: `24px` (1.5rem)
  - Buttons / Status Chips: `9999px` (Pill-shaped)

### Color Palette

| Token | CSS Variable | Hex / Value | Usage |
|---|---|---|---|
| Primary | `--color-primary` | `#65597b` | Active modules, primary CTA buttons |
| Primary Container | `--color-primary-container` | `#e6d6ff` | Highlight badges, active badge container |
| On-Primary | `--color-on-primary` | `#ffffff` | Text on primary buttons |
| Secondary | `--color-secondary` | `#426651` | Completion, positive stats, mint badges |
| Secondary Container | `--color-secondary-container` | `#c3ecd2` | Completed chips, high score highlights |
| Tertiary | `--color-tertiary` | `#6d5a59` | Soft alert tints, temporal cues |
| Background | `--color-background` | `#f8f9fa` | Page background |
| Surface | `--color-surface` | `#ffffff` | Base card background |
| On-Surface | `--color-on-surface` | `#191c1d` | Main heading / body text |
| On-Surface Variant | `--color-on-surface-variant` | `#49454d` | Subtitles, muted labels (60% opacity) |
| Outline | `--color-outline` | `#7a757e` | Card borders, subtle divider lines |
| Outline Variant | `--color-outline-variant` | `#cbc4ce` | Subtle borders, light input borders |
| Error / Alert | `--color-error` | `#ba1a1a` | Weak areas / needs focus accents |
| Error Container | `--color-error-container` | `#ffdad6` | Needs focus card light background |

---

## 📁 2. Frontend Directory Structure

```text
frontend/
├── public/
│   ├── favicon.svg
│   └── logo.svg
├── src/
│   ├── assets/                 # SVGs, icons, illustrations
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.jsx      # Top nav with brand logo, links, avatar & settings
│   │   │   └── PageWrapper.jsx # Max-width fluid container with gradient aura
│   │   ├── ui/                 # Atomic design tokens & reusable widgets
│   │   │   ├── Badge.jsx       # Status pill chips (Completed, In-Progress, Focus)
│   │   │   ├── Button.jsx      # Primary gradient pill & Ghost outlined buttons
│   │   │   ├── Card.jsx        # Glassmorphic card surface with frosted blur
│   │   │   ├── ProgressBar.jsx # Smooth animated CSS progress bar
│   │   │   └── StatCard.jsx    # Metric card with label, prominent number & trend
│   │   └── dashboard/
│   │       ├── LaunchPractice.jsx   # Quick start buttons (15-Q Mock & Custom JD)
│   │       ├── LastSessionCard.jsx  # Highlight of recent interview with score & CTA
│   │       ├── SessionsTable.jsx    # Historical practice sessions & feedback list
│   │       ├── StatsRow.jsx         # 4-card metric row (Readiness, Streak, Skills)
│   │       └── WelcomeBanner.jsx    # Candidate greeting + Readiness pill score
│   │   └── interview/
│   │       └── AvatarEva.jsx        # Animated female vector AI interviewer persona (Eva)
│   ├── hooks/
│   │   ├── useAuth.js          # Authentication state & JWT bearer token context
│   │   ├── useDashboard.js     # Orchestrates mock & live API telemetry
│   │   └── useReports.js       # Fetches Stage 4 multimodal reports
│   ├── pages/
│   │   ├── Dashboard.jsx       # 🚀 Phase 1 Core Candidate Home Surface
│   │   ├── Setup.jsx           # Phase 2A Practice track setup & upload form
│   │   ├── Interview.jsx       # Phase 2B Live voice conversation room & AvatarEva
│   │   ├── Report.jsx          # Phase 2C Multimodal evaluation dashboard
│   │   └── Login.jsx           # 🚀 Phase 2D Candidate authentication & signup
│   ├── services/
│   │   ├── api.js              # Central Axios instance with Bearer interceptors
│   │   ├── authService.js      # Login, Signup, /me endpoints
│   │   └── sessionService.js   # Session initiation & report fetching
│   ├── store/
│   │   └── authStore.js        # State management (Zustand)
│   ├── styles/
│   │   ├── animations.css      # Smooth keyframes, entrance & hover transitions
│   │   ├── glass.css           # Frosted glass, gradients & translucent layers
│   │   └── index.css           # CSS custom properties, Manrope font, resets
│   ├── utils/
│   │   ├── constants.js        # Default mock metrics & navigation routes
│   │   └── formatters.js       # Date, percentage, and text sanitizers
│   ├── App.jsx                 # Master application shell
│   ├── main.jsx                # React root bootstrap
│   └── router.jsx              # React Router v6 route configuration
├── .env.example                # VITE_API_URL=http://localhost:8000
├── index.html                  # HTML5 base with Manrope Google Fonts & Meta tags
├── package.json                # Project dependencies (React 18, Vite, Lucide, Axios)
└── vite.config.js              # Vite config with backend proxy (/api -> :8000)
```

---

## 🔄 3. Backend API Gateway Integration Map

| Frontend Component | HTTP / WS Action | Backend Endpoint | Data Delivered |
|---|---|---|---|
| `WelcomeBanner` & `Navbar` | `GET` | `/api/v1/auth/me` | Candidate name, email, profile role |
| `StatsRow` & `LastSessionCard` | `GET` | `/api/v1/reports/{session_id}` | Overall technical score, vocal delivery metrics |
| `SessionsTable` | `GET` | `/api/v1/questions/status/{id}` | Session progress, title, timestamp |
| `LaunchPractice` | `POST` | `/api/v1/setup/analyze` | Initiates Stage 1 & 2 interview prep |

*Note: For instant local testing without a running backend, a dual-mode fallback provider serves rich mock data matching the reference designs.*

---

## 🎬 4. Animation & Interaction Specifications (from `animate` skill)

1. **Card Entrances**:
   - Predetermined mounting entrance using GPU-accelerated `opacity` and `transform: translateY(8px)`.
   - Respects `@media (prefers-reduced-motion: reduce)`.
2. **Hover & Interactive Feedback**:
   - Duration: `150ms - 200ms` with `cubic-bezier(0.16, 1, 0.3, 1)`.
   - Subtle scale `1.015x` and soft shadow lift (`0 14px 32px rgba(101, 89, 123, 0.08)`).
3. **Progress Bar**:
   - Smooth width transition `width 800ms cubic-bezier(0.16, 1, 0.3, 1)` on initial render.
