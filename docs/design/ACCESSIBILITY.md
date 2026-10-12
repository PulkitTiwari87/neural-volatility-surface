# Accessibility

**Status:** PROPOSED (targets; nothing implemented or audited) · **Source:** MP §16 ("accessible tables or 2D alternatives", "accessible 2D alternatives") · **Canonical for:** accessibility requirements and test approach · **Parent:** [design.md](../../design.md) §16

## 1. Target
WCAG 2.2 Level AA as the working conformance target, verified by audit at Phase 5 (claims of conformance require an actual audit; until then the status is "targeted, not verified").

## 2. Requirements
| Area | Requirement |
|---|---|
| Alternatives to 3D | Every 3D visual has an equivalent keyboard- and screen-reader-accessible table and/or 2D heatmap of the same data with the same statuses (UI-009, UA-06). |
| Color | Status and scales are not color-only (pattern/marker/text); palettes validated for color-vision deficiencies and contrast (≥ AA text 4.5:1; non-text 3:1) in both themes. |
| Keyboard | All functionality via keyboard: selectors, chart navigation (arrow keys across nodes/points), pinning, toggles, camera reset, animation controls. Visible focus; no keyboard traps; logical order. |
| Screen readers | Charts have an accessible name, a short summary (what, range, trend, status mix), and a link to the data table; dynamic readouts announced politely; tables with proper headers and captions (units, n). |
| Motion | Respect `prefers-reduced-motion`: no autoplay; animation via explicit steps. No flashing. |
| Zoom & layout | 200% zoom and text-resize without loss of function; responsive reflow; no horizontal page scroll. |
| Targets | Interactive targets sized per WCAG 2.2 target-size guidance; pointer gestures have single-pointer alternatives (3D rotate has keyboard equivalent). |
| Errors & status | Errors/stale/partial states are textual, programmatically associated, and not color-only. |
| Language & units | Units spelled in accessible names ("implied volatility, percent"); abbreviations expanded on first use or via glossary link. |
| Themes | Dark/light themes both meet contrast; honors system contrast preferences where available. |

## 3. Process
- Design: accessibility acceptance criteria written per component before implementation.
- Build: automated checks in CI (linting for ARIA misuse, contrast tokens, axe-style scans) — tools chosen with DEC-008.
- Verify: manual keyboard-only walkthrough of the E2E journey; screen-reader spot checks on at least two reader/browser combinations; zoom and reduced-motion checks; record results in the Phase 5 gate.
- Maintain: regression tests for table alternatives and focus order.

## 4. Known tension
3D surfaces are inherently hard to make accessible; the commitment is **equivalent information via alternatives**, not an accessible 3D canvas.

## 5. Acceptance
UA-06 and UA-11 pass; audit report stored with the Phase 5 gate evidence; open issues listed in KNOWN_LIMITATIONS if any remain at release.
