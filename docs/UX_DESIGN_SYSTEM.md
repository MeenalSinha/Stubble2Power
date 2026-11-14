# Stubble2Power - User Experience (UX) & Design System

## 1. Design Philosophy: Modern Agricultural Glassmorphism
Stubble2Power combines high-technology satellite Earth observation with decentralized agricultural operations. The UI design system reflects this through a **Modern Agricultural Glassmorphism** aesthetic:
- **Depth and Clarity:** Frosted glass backgrounds (`backdrop-filter: blur(15px)`) layered over subtle environmental gradients.
- **Organic and Technical Harmony:** Deep forest greens and natural earth tones paired with crisp, technical data visualizations.
- **Purpose-Driven Restraint:** Elimination of unnecessary decorative visual noise in favor of data density and actionable insights.

---

## 2. Design Tokens

### 2.1 Color Palette
- **Primary Brand Forest:** `#2d5f3f` (Headers, active badges, navigation elements).
- **Secondary Sage Green:** `#5a9367` (Progress bars, highlights, confirmed metrics).
- **Glass Card Background:** `rgba(255, 255, 255, 0.70)` with `1px solid rgba(255, 255, 255, 0.50)`.
- **Sidebar Surface:** `rgba(163, 201, 168, 0.35)` with `backdrop-filter: blur(12px)`.
- **Text Primary:** `#1e462d` (Headings, metric values).
- **Text Body / Muted:** `#333333` / `#666666` (Prose, descriptions, captions).
- **Alert Success:** `rgba(212, 241, 221, 0.85)` with `#5a9367` accent border.
- **Alert Warning:** `rgba(255, 243, 205, 0.85)` with `#f9c74f` accent border.
- **Alert Critical:** `rgba(254, 226, 226, 0.85)` with `#ef4444` accent border.

### 2.2 Typography
- **Primary Font Family:** `'Inter', -apple-system, BlinkMacSystemFont, sans-serif`.
- **Indic Script Support:** Devanagari (Hindi) and Gurmukhi (Punjabi) rendered with native system fallbacks (`'Noto Sans Devanagari'`, `'Noto Sans Gurmukhi'`).
- **Font Weights:**
  - `300` (Light captions)
  - `400` (Body copy, table data)
  - `600` (Labels, table headers, button text)
  - `700` (Section headings, card titles)
  - `900` (Hero display metrics)

### 2.3 Component Elevation & Radii
- **Hero Section:** `border-radius: 25px`, `box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10)`.
- **Glass Cards:** `border-radius: 18px`, `padding: 1.8rem`, `box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08)`.
- **Buttons & Pills:** `border-radius: 20px`, `padding: 0.4rem 1rem`.

---

## 3. Strict Non-Emoji Rule (Rules 7 & 9)
In compliance with enterprise scientific and professional product standards, decorative emojis are strictly excluded from UI interfaces:
- **No Unicode Emojis:** Prohibited in page titles, navigation bars, button labels, metric cards, and alert headers.
- **Standardized Text Badges:** Statuses are communicated via clear, bracketed text badges:
  - `[OK]` (Operational / Normal)
  - `[WARN]` (Extended window / Moderate anomaly)
  - `[ALERT]` (Peak burn window / High anomaly)
  - `[VERIFIED]` (Verified landholder / Cross-sensor verified)
  - `[PENDING]` / `[PROCESSED]` (Operational dispatch status)

---

## 4. Multilingual Layout & Indic Typography
The interface dynamically adjusts layout constraints when switching between English, Hindi (हिन्दी), and Punjabi (ਪੰਜਾਬੀ):
- Line-height is maintained at a minimum of `1.5` to prevent clipping of upper and lower diacritics in Indic scripts.
- Text containers utilize flexbox and CSS grid with fluid wrapping to accommodate the roughly 15-20% length expansion typical of Indic translations.
- Core scientific metrics, NASA observation IDs, and chemical formulas (`CO2e`, `CH4`, `MW`, `kg/m3`) remain universally standardized across all languages.
