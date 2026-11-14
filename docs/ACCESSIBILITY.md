# Stubble2Power - Accessibility (a11y) & WCAG 2.2 AA Compliance

## 1. Commitment to Accessible Design
Stubble2Power is designed to be accessible to diverse users—including rural farmers accessing mobile devices in low-connectivity areas, field operators using rugged tablets, and analysts using high-resolution desktop displays. The platform conforms to the **Web Content Accessibility Guidelines (WCAG) 2.2 Level AA**.

---

## 2. Accessibility Pillars & Compliance Audit

### 2.1 Color Contrast Compliance (WCAG 1.4.3 & 1.4.11)
All text, interactive controls, and visual boundaries exceed WCAG Level AA contrast ratios:
- **Primary Body Text (`#1e462d` on `#ffffff`):** Contrast ratio of **10.4:1** (Exceeds 4.5:1 requirement).
- **Secondary Headings (`#2d5f3f` on `#ffffff`):** Contrast ratio of **7.6:1** (Exceeds 4.5:1 requirement).
- **Glass Card Backgrounds (`rgba(255,255,255,0.70)` on `#f5f7fa`):** Subtle boundaries supplemented by explicit `1px solid rgba(45,95,63,0.2)` borders.
- **Form Inputs and Buttons:** Minimum 3:1 contrast against adjacent backgrounds.

### 2.2 Color-Independent Status Indicators (WCAG 1.4.1)
Color is never used as the sole conveyor of information. All status alerts, system health monitors, and operational indicators include explicit textual descriptors:
- `[OK]` (Operational, Normal, Verified)
- `[WARN]` (Extended harvest window, Moderate anomaly)
- `[ALERT]` (Active peak burn window, High anomaly, Severe risk)
- `[PENDING]`, `[ARRIVED]`, `[PROCESSED]` (Route dispatch status)

### 2.3 Keyboard Operability (WCAG 2.1.1 & 2.4.7)
- **Logical Tab Order:** Interactive controls (forms, selects, buttons, radio options) follow a logical reading order top-to-bottom and left-to-right.
- **Focus Visibility:** Focused elements display a high-contrast outline (`2px solid #2d5f3f` with `offset: 2px`).
- **No Keyboard Traps:** Modal dialogs and dropdown menus allow forward and backward tabbing and escape via the `ESC` key.

### 2.4 Screen Reader Compatibility (WCAG 4.1.2)
- **Semantic Structure:** Native HTML5 landmark elements (`<main>`, `<aside>`, `<nav>`, `<header>`, `<footer>`) and strict heading hierarchies (`h1` through `h4`) are enforced.
- **Alternative Data Representations:** Interactive Folium spatial maps and Plotly charts are accompanied by tabular data views (`st.dataframe`) ensuring full programmatic access for screen reader users.
- **Descriptive Form Labels:** All input elements feature explicit, visible `<label>` text and descriptive help attributes.

### 2.5 Indic Multilingual Typography & Scaling (WCAG 1.4.4)
- Text containers are built with dynamic flexbox layouts supporting up to **200% font zoom** without content truncation or horizontal scrolling.
- Hindi and Punjabi Indic scripts utilize standardized system typefaces ensuring crisp glyph rendering and proper ligatures.
