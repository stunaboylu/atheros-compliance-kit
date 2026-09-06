# AtherosAI Compliance Kit — Brand Kit

> Phase 2. Consumes `artifacts/positioning.md`. Feeds the Expo console (`console/`), the CLI's
> terminal output, and every generated report (Markdown/HTML/PDF).
>
> **Relationship to the AtherosAI Platform brand kit.** Same house. Identical semantic layer —
> risk-tier and status colours are *inherited unchanged* so a screenshot from the Kit and a
> screenshot from the Platform mean the same thing. What differs is the base: the Platform is a
> system of record for auditors (dark-only, dense tables); the Kit is a developer tool that lives
> beside an IDE and a terminal, so it is **dual-theme** and its neutral is warmer.

## Console chrome: Argon

The Console's chrome — surfaces, typography, shadows, radii, the indigo accent, the gradient
hero, the sidebar and the stat cards — follows the **Argon Dashboard** design system. Concretely:

| | |
|---|---|
| Typeface | Open Sans 300/400/600/700 (mono stays JetBrains Mono) |
| Accent | `#5E72E4` indigo, hover `#324CDD` |
| Text | `#172B4D` primary · `#525F7F` muted · `#8898AA` faint |
| Page | `#F8F9FE`, cards `#FFFFFF` |
| Depth | Layered soft shadows (`0 .25rem .375rem -.0625rem rgba(20,20,20,.12)` + a second pass), not hairline borders |
| Radii | 6 / 8 / 12 / 16, generous by house standards |
| Hero | `linear-gradient(87deg, #172B4D → #1A174D)` with the content cards overlapping it |

**The semantic layer does NOT follow Argon, deliberately.** Argon's `#F5365C` error and `#2DCE89`
success are the same hues one step more saturated than the risk-tier colours below. Adopting them
would look marginally better and would silently break the 1:1 correspondence with
`atheros_kit`'s Python enums and with the AtherosAI Platform's palette — after which a screenshot
from the Kit and one from the Platform would no longer mean the same thing.

> Chrome is a style choice. A risk colour is a data type.

## Design principles

1. **Evidence over decoration.** Every colour carries semantic meaning (risk, status, gate).
   No colour used aesthetically where it could be read as a signal.
2. **Terminal parity.** Anything the console shows in colour, the CLI shows in ANSI-16 with the
   same meaning and a text label. A CI log is a first-class surface, not a downgrade.
3. **Uncertainty is a visual state, not a missing one.** `grey-zone`, `unknown`, and `degraded`
   have their own tokens. A tool that renders "unknown" as "fine" is a broken instrument.
4. **Dual theme, single semantics.** Light for docs/day, dark for console/IDE. Only the base
   surfaces swap; the semantic layer is theme-invariant by design.

## Colour tokens

### Base surfaces — dark (console default)
| Token | Hex | Use |
|---|---|---|
| `--bg` | `#0B0F17` | Root background |
| `--surface` | `#161B26` | Cards, panels, table containers |
| `--surface-2` | `#1E2534` | Raised surface, hover rows, popovers |
| `--surface-3` | `#28304199` | Subtle fills, skeletons, disabled |
| `--border` | `#2A3345` | Hairline borders |
| `--border-strong` | `#3A4560` | Emphasised dividers, focused card outline |
| `--text` | `#E6EAF2` | Primary text |
| `--text-muted` | `#9AA4B8` | Secondary / labels |
| `--text-faint` | `#6B7488` | Captions / placeholders |

### Base surfaces — light (docs / reports / print)
| Token | Hex | Use |
|---|---|---|
| `--bg` | `#FBFBFD` | Root background |
| `--surface` | `#FFFFFF` | Cards, report body |
| `--surface-2` | `#F3F4F8` | Raised / zebra rows |
| `--surface-3` | `#EAECF2` | Subtle fills |
| `--border` | `#DFE2EA` | Hairline borders |
| `--border-strong` | `#C3C8D4` | Emphasised dividers |
| `--text` | `#111726` | Primary text |
| `--text-muted` | `#525A6B` | Secondary |
| `--text-faint` | `#7A8296` | Captions |

### Accent
| Token | Dark | Light | Use |
|---|---|---|---|
| `--accent` | `#3B82F6` | `#2563EB` | Primary buttons, links, active nav, focus ring |
| `--accent-hover` | `#2F6FE0` | `#1D4ED8` | Hover |
| `--accent-subtle` | `#3B82F61A` | `#2563EB14` | Selected row tint, badge bg, chart area fill |
| `--accent-border` | `#3B82F659` | `#2563EB4D` | Active input border, selected card border |

### Semantic — EU AI Act risk tiers (theme-invariant; **MUST** map 1:1 to `euact.RiskTier`)
| Tier enum | Token | Hex | ANSI (CLI) |
|---|---|---|---|
| `unacceptable` | `--risk-unacceptable` | `#DC2626` | bright red |
| `high` | `--risk-high` | `#F97316` | yellow/orange |
| `limited` | `--risk-limited` | `#EAB308` | yellow |
| `minimal` | `--risk-minimal` | `#22C55E` | green |
| `unknown` | `--risk-unknown` | `#6B7488` | dim/grey |
| *grey-zone overlay* | `--grey-zone` | `#A855F7` | magenta | diagonal-hatch overlay on the tier colour + `?` glyph |

> **Rule.** `--grey-zone` is an **overlay**, never a replacement. A grey-zone HIGH is still drawn
> high-orange, hatched, with the tier label and the word `grey zone`. Removing the tier colour
> would hide the classification the engine actually reached.

### Semantic — guardrail actions (**MUST** map 1:1 to `guard.Action`)
| Action | Token | Hex | Glyph |
|---|---|---|---|
| `pass` | `--action-pass` | `#22C55E` | `✓` |
| `flag` | `--action-flag` | `#EAB308` | `!` |
| `block` | `--action-block` | `#DC2626` | `⨯` |

### Semantic — status / severity / findings
| Token | Hex | Use |
|---|---|---|
| `--severity-critical` | `#DC2626` | Critical finding |
| `--severity-high` | `#F97316` | High |
| `--severity-medium` | `#EAB308` | Medium |
| `--severity-low` | `#3B82F6` | Low / info |
| `--success` | `#22C55E` | Passed gate, chain valid, covered |
| `--warning` | `#EAB308` | Needs review, partial, stale |
| `--danger` | `#DC2626` | Failed gate, chain violation, revoked |
| `--info` | `#38BDF8` | Neutral informational, running |
| `--degraded` | `#A855F7` | **LLM path unavailable — deterministic fallback ran** |

> `--degraded` is unique to the Kit. It answers "was this number produced the good way?" and must
> appear on any score whose `method` field is not the primary one.

### Coverage (evidence)
`covered` `#22C55E` · `partial` `#EAB308` · `missing` `#DC2626` · `not_applicable` `#6B7488`

### Score scale (Fairness Score, compliance score, 0–100)
Thresholded, **not** a linear rainbow: `≥85` `#22C55E` · `70–84` `#EAB308` · `50–69` `#F97316` ·
`<50` `#DC2626` · `null/unmeasured` `#6B7488` (never green — unmeasured is not good).

### Data-viz categorical (colourblind-aware, ordered)
`#3B82F6` · `#22C55E` · `#F97316` · `#A855F7` · `#38BDF8` · `#EAB308` · `#EC4899` · `#14B8A6`
- Sequential: `#0B0F17 → #1E3A8A → #3B82F6 → #93C5FD`
- Diverging (drift ±): `#DC2626 ← #6B7488 → #22C55E`
- Grid lines `--border` @40%; axis labels `--text-faint`.

## Typography
- **Sans (UI):** `Inter`, system-ui fallback. 400/500/600/700.
- **Mono (identifiers, hashes, code, article numbers, module paths):** `JetBrains Mono`,
  `ui-monospace` fallback. Chain hashes, `session_id`, `Art. 15`, `atheros_kit.guard` are
  **always** mono.
- Scale (rem): `12 / 13 / 14(base) / 16 / 18 / 20 / 24 / 30 / 36`. Body 14, table cell 13, caption 12.
- Line-height: 1.5 body · 1.35 headings · 1.7 long-form (dossier clause text).
- `font-variant-numeric: tabular-nums` on every score, metric, and table numeral.

## Spacing & shape
- Spacing (px): `2 4 8 12 16 20 24 32 40 48 64`.
- Radius: `--r-sm 6` (badges, inputs) · `--r-md 10` (cards, buttons) · `--r-lg 14` (panels, modals) ·
  `--r-full 999` (pills).
- Card padding 20–24 · table row 44 · control height 36 (sm) / 40 (md).
- Dark: elevation via surface + 1px border, not heavy shadow. Modal `0 16px 48px #0006`.

## Component conventions
- **RiskBadge** — pill; tier colour as text + `-subtle` bg + 1px tier border. Uppercase 12px/600.
  Grey-zone adds hatch + `?`.
- **ActionPill** — guardrail action; glyph + label, never colour alone.
- **ScoreRing / ScoreBar** — 0–100, thresholded palette; `null` renders as a grey dashed ring
  reading `unmeasured`, never an empty green ring.
- **MethodTag** — small mono tag on any computed score: `llm` · `deterministic` · `hybrid`.
  `deterministic` where an LLM was configured renders `--degraded`.
- **ChainBadge** — ledger integrity: `intact` (`--success`, mono short hash) / `violated`
  (`--danger`, line numbers) / `unverified` (`--text-faint`).
- **ArticleChip** — mono, `Art. 15` / `Annex III`; links to the dossier section anchor.
- **FindingRow** — severity dot + check name (mono) + one-sentence detail + evidence pointer.
- **DataTable** — zebra `--surface`/`--surface-2`, sticky header, mono IDs, right-aligned
  tabular numbers, hover `--accent-subtle`.
- **Focus ring** — 2px `--accent`, 2px offset, on every interactive element.

## CLI (terminal surface)
```
atheros-kit euact classify --spec system.json
  ✓  pass      guardrail input gate            (2 checks)
  !  flag      pii: email, iban                Art. 10
  ⨯  block     prompt_injection                instruction-override phrasing
  ▮  HIGH      grey zone (2 Annex III matches) Annex III · Art. 6(2)   conf 0.65
```
- ANSI-16 only (CI logs mangle 256-colour). `NO_COLOR` honoured; glyphs carry the meaning alone.
- Every line: **glyph · label · detail · article**. Never colour without a word.

## Accessibility
- Contrast ≥ 7:1 body on `--bg`/`--surface`, both themes.
- Never colour alone for risk/status/action — always paired with a label or glyph.
- Charts ship an accessible summary + table fallback.
- `prefers-reduced-motion` kills pulses and transitions.

## Voice (microcopy)
- Factual, standards-anchored, non-alarmist. "Evidence missing — Art. 15", not "Uh oh!".
- English primary, Turkish parity. Never mix languages in one view.
- **Never**: "certified", "guaranteed compliant", "fully compliant", "no further action required".
  This is enforced by a lint over product copy and generated reports, not by good intentions.
