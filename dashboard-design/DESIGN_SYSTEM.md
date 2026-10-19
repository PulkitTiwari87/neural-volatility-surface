# Design system

**Status:** `PROPOSED`. Values below are chosen and contrast-checked here; they supersede the "values `OPEN`" note in [../docs/design/DESIGN_SYSTEM.md](../docs/design/DESIGN_SYSTEM.md), whose token *roles* and formatting rules remain canonical and are reused unchanged. The Stitch design systems are `assets/15502535519750022530` (dark) and `assets/2088746606350607947` (light); where the mocks differ from this file, **this file wins**.

## 1. Principles

1. Status is never colour alone; every status has a distinct icon shape and a text label.
2. Hierarchy comes from scale, weight and tone steps, not borders. Borders only where a tone step cannot separate.
3. One accent. Amber and red are semantic status colours, not accents.
4. Monospace is for identifiers (run ids, hashes, dataset ids, tenor values in segmented controls). Never for prose or table headers.
5. Nothing under 13px. Body 15px (workbench) and 18px (landing).
6. No gradients (the continuous diverging legend is the one exception, because it is a scale), no glow, no glass, no decorative charts.

## 2. Colour tokens (contrast computed with the WCAG 2.x formula)

### Dark (workbench)

| Token | Value | Use | Contrast on `surface-1` `#121821` |
|---|---|---|---|
| `bg-base` | `#0C1016` | App background | n/a |
| `surface-1` | `#121821` | Panels | n/a |
| `surface-2` | `#18202B` | Raised, table header | n/a |
| `surface-3` | `#202A37` | Hover, selected row | n/a |
| `border-subtle` | `#2A3544` | Only where tone steps fail | decorative |
| `text-primary` | `#E6EBF2` | Body, values | 14.88 |
| `text-secondary` | `#A7B2C2` | Supporting text | 8.31 |
| `text-muted` | `#7D8999` | Metadata only (never the only carrier of meaning) | 5.02 (4.62 on `surface-2`) |
| `accent` | `#86C8E8` | Primary action, active nav, focus ring, selection | 9.71 (10.39 on `bg-base`) |
| `on-accent` | `#0C1016` | Text on accent fill | 10.39 |

### Light (landing, documentation reading)

| Token | Value | Use | Contrast on ground `#F3F5F7` |
|---|---|---|---|
| `ground` | `#F3F5F7` | Page | n/a |
| `surface` | `#FFFFFF` | Quiet raised areas | n/a |
| `step` | `#E8ECF0` | Alternate section field | n/a |
| `ink` | `#111722` | Headlines, body | 16.43 |
| `slate` | `#4B586A` | Supporting text | 6.62 (6.09 on `step`) |
| `accent-light` | `#1F6F99` | Links, emphasis, focus ring | 5.07 (4.66 on `step`) |
| `plate` | `#0C1016` | Dark instrument plate (same as `bg-base`) | n/a |

### Status (text colours; each also needs its icon and label)

| Status | Dark value (on `#121821`) | Light value (on `#F3F5F7` / `#E8ECF0`) | Icon shape |
|---|---|---|---|
| Completed | `#5FB589` (7.18) | `#276B49` (5.85 / 5.38) | Check in circle |
| In progress | `#E0A53A` (8.16) | `#8A5A0E` (5.41 / 4.98) | Half-filled ring |
| Planned | `#8A9BB5` (6.31) | `#4F5F7A` (5.91 / 5.44) | Dashed ring |
| Blocked | `#E5675E` (5.46) | `#A93A33` (5.75 / 5.30) | Octagon with bar |
| Unavailable | `#8C97A8` (6.03) | `#5A6575` (5.41 / 4.98) | Slashed circle |
| Unverified | `#C9B26B` (8.54) | `#75621C` (5.46 / 5.02) | Ring with question mark |
| Failed | `#E5675E` (5.46) | `#A93A33` (5.75 / 5.30) | Filled cross |

Blocked and Failed share a hue but differ by icon and label. The first-pass values used in the Stitch mocks (`#6B7686` for Unavailable in dark; `#A8741C`, `#2F7D57`, `#6B7686`, `#8A7424` in light) fail 4.5:1 as text on some surfaces and are not to be used.

**Semantics (never conflate):** *Unverified* is not *Failed*; *Planned* is not *Completed*; *Unavailable* means the source or capability is absent; *Blocked* means something specific prevents progress. The UI never shows `VALIDATED`; nothing in the project has reached it.

### Source chips (data origin of a value)

`Documented` (read from project documents; quiet: small, no fill, muted text), `Live from run` (read from the research API; accent text), `Not connected` (no source reachable; Unavailable styling). State chips lead visually; source chips are secondary.

### Cell status encodings (colour and pattern, both required)

Statuses come from `backend/src/volatility_lab/surfaces/grid.py`: `observed`, `interpolated_T`, `interpolated_k`, `missing` (plus `predicted` for forecast cells, a UI-only concept).

| Status | Fill | Pattern (must be present) | Dark token | Light token |
|---|---|---|---|---|
| Observed | Solid | none | `#86C8E8` at full | `#1F6F99` |
| Interpolated in tenor | Tinted | Diagonal hatch, 45 degrees | `#86C8E8` hatch on `surface-2` | `#1F6F99` hatch on `step` |
| Interpolated in strike | Tinted | Dotted | dots on `surface-2` | dots on `step` |
| Missing | Empty | Dashed outline and an em dash | outline `#7D8999` | outline `#5A6575` |
| Predicted | Solid graphite | Solid ice outline | `#18202B` + `#86C8E8` outline | ink fill + accent outline |

Extrapolated is hidden by default in the design language ([../docs/design/VISUALIZATION_SPEC.md](../docs/design/VISUALIZATION_SPEC.md) V1) and does not exist in the current code (cells are never extrapolated).

Quantity scales: **sequential IV** (one hue, light to dark, for level); **diverging difference** (forecast minus actual): negative `#5AA9E6`, neutral `#1B222C`, positive `#E8924A`, zero-centred with symmetric limits by default (non-text contrast against neutral: 6.29 and 6.59). Categorical series (model comparison): at most 4 hues in fixed order; validate with the dataviz palette validator before use (not yet run).

## 3. Typography

| Role | Face | Size / weight / tracking | Notes |
|---|---|---|---|
| Landing display | Geist | 72 to 88px, 600, -0.035em, leading 0.98 | at most two lines |
| Landing section | Geist | 40px, 600, -0.02em | |
| Landing body | Geist | 18px/1.6, 400 | 62 characters |
| Workbench page title | Geist | 32px, 600, -0.02em | |
| Workbench section | Geist | 20px, 600 | |
| Workbench body | Geist | 15px/1.55, 400 | 68 characters |
| Table / data | Geist, tabular figures | 14px, right-aligned numbers | |
| Label / header | Geist | 13px, 500, sentence case | no tiny uppercase tracked labels |
| Identifier | JetBrains Mono (the Stitch option; Geist Mono is the preferred pairing if available) | 13px, 500 | run ids, hashes, dataset ids |

Fallback stack: `Geist, system-ui, -apple-system, "Segoe UI", sans-serif`; mono: `"JetBrains Mono", ui-monospace, Consolas, monospace`. **Font delivery constraint:** the current server CSP (`default-src 'none'`) blocks Google Fonts and any font file. Fonts must be self-hosted and the CSP extended with `font-src 'self'`, or the system fallback is used ([IMPLEMENTATION_PLAN §7](IMPLEMENTATION_PLAN.md)). The licences of Geist and JetBrains Mono need confirming before bundling; not checked here.

## 4. Spacing, shape, surfaces

8px scale (4, 8, 12, 16, 24, 32, 48, 64, 96, 128). Component radius 8px, panel radius 12px, chips 6px. Panels: `surface-1` on `bg-base`, 20 to 24px padding, no shadow at rest. Shadows only on what floats (menu, dialog, tooltip). Table rows 48px; no cell grid lines. Landing section gap 120 to 160px; workbench panel gap 24px. Sidebar 232px; content max width 1440px.

## 5. Components

Examples are on the Stitch "Components and states" board (`87b01e179b024dc69563d93847bef14d`). Required set and rules:

| Component | Rules |
|---|---|
| Navigation | Sidebar: icon plus full text label (no abbreviations), active item uses accent text and `surface-3`; "Back to home" at the bottom. Mobile: a "Menu" button opens a full-height sheet. |
| Context bar | Run, data origin, research-API connection, units. Always visible. Plain sentence text in Geist. |
| Buttons | Primary: accent fill, `on-accent` text, 8px radius. Secondary: `surface-2` fill. Tertiary: text link with arrow. Pressed: 1px translate. Minimum target 44px. |
| Tabs / segmented | Underline in accent for tabs; segmented control for tenor values (mono digits). Arrow-key navigation. |
| Status chip | Icon + label, 6px radius, state colour for text and icon, `surface-2` fill. |
| Source chip | As above; quieter than state chips. |
| Tooltip | Opens on hover and focus; shows tenor, log-moneyness, IV in stated units, status, quote count. Never the only place a value appears. |
| Table | Sentence-case headers, right-aligned tabular numbers, an `n` column where counts exist, insufficient-n marker, sticky header, keyboard-focusable cells for surface tables. |
| Metric summary | Label, value (or em dash), unit, `n`, source chip. |
| Chart panel | Title, units in the title, legend with patterns, table toggle, source chip. |
| Filters / selectors | Run, date, model; visible labels above fields. |
| Date control | Slider plus previous and next steppers and a readout "Date n of N"; stepping, not tweening, across gaps. |
| Loading | Skeleton blocks matching the final layout; no spinners. |
| Empty | What is missing, why, what to do. |
| Error | Inline, icon and text, with Retry; no raw URLs or stack traces. |
| Unavailable data | "Not available. Source: ..." naming the missing source. |
| Validation warning | Amber banner with icon and text; stays until the condition clears. |
| Confirmation dialog | Only for destructive or irreversible actions; labelled buttons ("Keep", "Discard"); focus trapped and returned. The workbench is read-only today, so dialogs are rare. |

## 6. Chart conventions

Axis titles carry units ("Implied volatility (vol points)", "Log-moneyness k", "Tenor (days)"); IV is stored as decimal and displayed in vol points, stated each time ([../CLAUDE.md](../CLAUDE.md) §6). Missing is "—" plus status, never 0. Every aggregate shows `n`. Heatmap cells below the minimum count are hatched "insufficient" (`MIN_CELLS = 100` is a research setting, [IMPLEMENTATION_MATRIX](../docs/engineering/IMPLEMENTATION_MATRIX.md) P3). Forecast uses the same grid, scale and limits as actual; difference uses the diverging scale. Charts are SVG (heatmap, slices, error bars) with a table equivalent; the 3D surface is specified in [WORKBENCH §5](WORKBENCH.md).

## 7. Responsive rules

Breakpoints (proposed): 390 (phone), 768 (tablet), 1024, 1440. Below 768 all multi-column layouts collapse to one column; no horizontal page scroll; tables scroll inside their own container with a visible edge cue. On phones the Surface Explorer defaults to **Heatmap** (the 3D view is secondary on touch devices; the ui-ux-pro-max chart guidance lists mobile as a context to avoid 3D). Tap targets at least 44px. Headlines scale with `clamp()`. Tablet keeps a collapsed icon rail with labels on expand.

## 8. Accessibility requirements

Target: WCAG 2.2 AA, *targeted not verified* ([../docs/design/ACCESSIBILITY.md](../docs/design/ACCESSIBILITY.md); a conformance claim needs an audit). Specific to this design:

- Contrast: all tokens above meet 4.5:1 for text and 3:1 for non-text on their intended surfaces; muted text is metadata only.
- Status: icon shape plus label plus (for cells) pattern; passes without colour.
- Focus: 2px accent ring with 1px offset on every control, never removed; not obscured by sticky bars.
- Keyboard: arrow keys move between heatmap cells with a polite live-region readout; a 3D view has Rotate, Zoom and Reset buttons and arrow-key camera control.
- Motion: durations 150 to 250ms ease-out, opacity and transform only; `prefers-reduced-motion` removes travel; no autoplay; `prefers-contrast: more` raises borders. Nothing is translucent, so `prefers-reduced-transparency` needs no special handling.
- Charts: accessible name, a summary sentence (what, range, status mix), and a link to the table.
- Forced colours: patterns and outlines survive; icons use `currentColor`.
- 200% zoom and text resize without loss of function.

## 9. Not decided here

Brand mark (the wordmark glyph in the mocks is a placeholder grid icon), final icon set (one consistent line set, light to regular stroke), theme-toggle persistence, print styles, licences of bundled fonts.
