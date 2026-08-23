# Netran AI — Frontend Architecture & Structure Specification

This document details the architecture, design tokens, component hierarchy, directory layout, and API integration contracts for the **Netran AI** web frontend client.

---

## 🎨 1. Design Tokens & Visual Architecture (from `DESIGN.md`)

* **Theme Name**: Serene Learning (Modern Glassmorphism)
* **Design Personality**: Empathetic, calm, intellectually stimulating digital sanctuary.
* **Typography**: **Manrope** (Google Fonts)
* **Icon Standard**: 100% Vector Icon Libraries (`lucide-react`) per Rule 15. Raw text emojis are strictly prohibited in structural UI.
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
│   └── pcm-processor.js        # AudioWorklet downsampling 48kHz native audio to 16kHz PCM
├── src/
│   ├── assets/                 # SVGs, vector illustrations
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.jsx      # Top nav with brand logo, routes, notifications tray & profile menu
│   │   │   └── PageWrapper.jsx # Max-width fluid container with gradient aura
│   │   ├── ui/                 # Atomic design tokens & reusable widgets
│   │   │   ├── Badge.jsx       # Status pill chips (Completed, In-Progress, Focus)
│   │   │   ├── Button.jsx      # Primary gradient pill & Ghost outlined buttons
│   │   │   ├── Card.jsx        # Glassmorphic card surface with frosted blur
│   │   │   ├── ProgressBar.jsx # Smooth animated CSS progress bar
│   │   │   └── StatCard.jsx    # Metric card with label, prominent number & trend
│   │   ├── dashboard/
│   │   │   ├── LaunchPractice.jsx   # Quick start buttons (15-Q Mock & Custom JD)
│   │   │   ├── LastSessionCard.jsx  # Highlight of recent interview with score & CTA
│   │   │   ├── SessionsTable.jsx    # Historical practice sessions & feedback list
│   │   │   ├── StatsRow.jsx         # 4-card metric row (Readiness, Streak, Skills)
│   │   │   ├── TemplatePicker.jsx   # Personalized pre-built template interview modal
│   │   │   └── WelcomeBanner.jsx    # Candidate greeting + Readiness pill score
│   │   └── interview/
│   │       └── AvatarEva.jsx        # Animated vector AI interviewer with speaking pulse wave
│   ├── hooks/
│   │   ├── useAuth.js          # Authentication state & JWT bearer token context
│   │   ├── useDashboard.js     # Orchestrates mock & live API telemetry
│   │   ├── useInterviewSession.js # Full-duplex WebSocket audio & live transcript accumulator
│   │   ├── useReports.js       # Fetches Stage 4 multimodal reports
│   │   └── useSetup.js         # Handles resume/JD ingestion and pipeline status polling
│   ├── pages/
│   │   ├── Dashboard.jsx       # Candidate home hub & quick launchpad
│   │   ├── Setup.jsx           # Practice track configuration & document upload
│   │   ├── Interview.jsx       # Live voice interview room, controls & live transcript modal
│   │   ├── Processing.jsx      # Post-session evaluation progress animation screen
│   │   ├── Report.jsx          # Multimodal evaluation report & telemetry scorecard
│   │   ├── Login.jsx           # Candidate authentication & registration
│   │   ├── History.jsx         # Session archives, question logs, and filterable table
│   │   ├── Analytics.jsx       # Competency radar, readiness progression, and performance charts
│   │   └── Settings.jsx        # Candidate profile (display_name) and password management
│   ├── services/
│   │   ├── api.js              # Central Axios instance with Bearer interceptors
│   │   ├── authService.js      # Login, Signup, /me, updateProfile, changePassword
│   │   ├── sessionService.js   # Ingestion, session creation & status polling
│   │   ├── templateService.js  # Pre-built interview templates (/template/list, /template/start)
│   │   ├── reportService.js    # Multimodal report generation & retrieval
│   │   ├── analyticsService.js # Performance aggregates & radar telemetry
│   │   ├── historyService.js   # Historical session archives & detail views
│   │   └── notificationsService.js # DB-backed candidate notifications & read state sync
│   ├── store/
│   │   └── authStore.js        # Global authentication store (Zustand)
│   ├── styles/
│   │   ├── animations.css      # Keyframes, entrance effects, speaking pulse waves
│   │   ├── glass.css           # Frosted glass, gradients & translucent layers
│   │   └── index.css           # CSS custom properties, Manrope font, resets
│   ├── utils/
│   │   ├── constants.js        # Default mock metrics & navigation routes
│   │   └── formatters.js       # Relative time, percentage, and text formatters
│   ├── App.jsx                 # Master application shell
│   ├── main.jsx                # React root bootstrap
│   └── router.jsx              # React Router v6 route configuration with auth guards
├── index.html                  # HTML5 base with Manrope Google Fonts & Meta tags
├── package.json                # Project dependencies (React 18, Vite, Lucide, Axios)
└── vite.config.js              # Vite config with backend proxy (/api -> :8000)
```

---

## 🔄 3. Backend API Gateway Integration Map

| Frontend Component / Page | HTTP / WS Action | Backend Endpoint | Data Delivered |
|---|---|---|---|
| `Navbar` | `GET` / `POST` / `PATCH` | `/api/v1/notifications` | Unread notifications, mark read, relative time |
| `Settings` | `PATCH` / `POST` | `/api/v1/auth/profile`<br>`/api/v1/auth/change-password` | Updates candidate display name & password |
| `Interview` Room | `WS` | `/api/v1/voice/stream/{id}` | Bidirectional 16kHz PCM audio & turn transcript |
| `TemplatePicker` | `GET` / `POST` | `/api/v1/template/list`<br>`/api/v1/template/start` | Pre-built templates list & personalized mock launch |
| `History` Page | `GET` | `/api/v1/history/sessions`<br>`/api/v1/history/detail/{id}` | Session archives, transcripts, and question trees |
| `Analytics` Page | `GET` | `/api/v1/analytics/summary` | Readiness trends, skill radar, and pacing metrics |
| `Report` Scorecard | `GET` | `/api/v1/reports/{id}` | Multimodal scores, audio waveform, and feedback |
| `Setup` Page | `POST` | `/api/v1/ingest/resume`<br>`/api/v1/setup/analyze` | Document parsing & Stage 1-2 pipeline triggers |

---

## 🎬 4. Key Interactive Components

1. **Live Interview Dialogue Transcript Panel**:
   - Built into `Interview.jsx` with real-time dialogue accumulation from WebSocket turn events.
   - Distinct left/right bubbles for Eva (with topic tags) and candidate, with automatic smooth scroll.
2. **Synchronized Eva Speaking Avatar**:
   - `AvatarEva.jsx` features talking mouth morphing, natural breathing, and dynamic acoustic glowing ripple pulses synced to `isSpeaking`.
3. **Audio Streaming Architecture**:
   - `pcm-processor.js` runs in an `AudioWorklet` to downsample native browser audio to 16-bit 16kHz PCM chunks for Silero VAD without driver artifacts.
