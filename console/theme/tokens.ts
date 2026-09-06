/**
 * Design tokens — Argon.
 *
 * The chrome (surfaces, type, shadows, radii, the indigo accent) follows the
 * Argon Dashboard design system, because that is the visual language this
 * product is being held to.
 *
 * The SEMANTIC layer does not follow Argon, and that is deliberate. Risk tiers,
 * guard actions and score bands map 1:1 onto Python enums and onto the AtherosAI
 * Platform's palette, so a screenshot from the Console and one from the Platform
 * mean the same thing. Argon's error red and success green are the same hues
 * one step more saturated; adopting them would look marginally better and would
 * silently break that correspondence. Chrome is a style choice. A risk colour is
 * a data type.
 */

// ── Argon base ────────────────────────────────────────────────────────────────
export const light = {
  bg: '#F8F9FE',
  surface: '#FFFFFF',
  surface2: '#F7FAFC',
  surface3: '#EDF1F7',
  border: '#E9ECEF',
  borderStrong: '#CAD1D7',
  text: '#172B4D',
  textStrong: '#0B1A36',
  textMuted: '#525F7F',
  textFaint: '#8898AA',
  accent: '#5E72E4',
  accentHover: '#324CDD',
  accentSubtle: 'rgba(94,114,228,0.10)',
  accentBorder: 'rgba(94,114,228,0.35)',
  onAccent: '#FFFFFF',
  gradientFrom: '#172B4D',
  gradientTo: '#1A174D',
} as const;

export const dark = {
  bg: '#0F1116',
  surface: '#1A1D24',
  surface2: '#22262F',
  surface3: '#2B303A',
  border: '#2B303A',
  borderStrong: '#3C4350',
  text: '#E9ECF2',
  textStrong: '#FFFFFF',
  textMuted: '#A7B0C0',
  textFaint: '#7C8698',
  accent: '#8392EE',
  accentHover: '#5E72E4',
  accentSubtle: 'rgba(131,146,238,0.14)',
  accentBorder: 'rgba(131,146,238,0.40)',
  onAccent: '#0F1116',
  gradientFrom: '#141B2E',
  gradientTo: '#171533',
} as const;

export type Palette = { readonly [K in keyof typeof light]: string };

/** Theme-invariant. Never redefine per theme — the meaning must not move. */
export const semantic = {
  riskTier: {
    unacceptable: '#DC2626',
    high: '#F97316',
    limited: '#EAB308',
    minimal: '#22C55E',
    unknown: '#8898AA',
  },
  /** An OVERLAY on the tier colour, never a replacement. */
  greyZone: '#A855F7',
  action: { pass: '#22C55E', flag: '#EAB308', block: '#DC2626' },
  severity: {
    critical: '#DC2626',
    high: '#F97316',
    medium: '#EAB308',
    low: '#5E72E4',
    info: '#11CDEF',
  },
  band: {
    good: '#22C55E',
    watch: '#EAB308',
    poor: '#F97316',
    critical: '#DC2626',
    /** Unmeasured is grey and never green. */
    unmeasured: '#8898AA',
  },
  coverage: {
    covered: '#22C55E',
    partial: '#EAB308',
    missing: '#DC2626',
    not_applicable: '#8898AA',
  },
  degraded: '#A855F7',
  success: '#2DCE89',
  warning: '#FB6340',
  danger: '#F5365C',
  info: '#11CDEF',
} as const;

export const glyph = {
  action: { pass: '✓', flag: '!', block: '⨯' },
  severity: { critical: '⨯', high: '▲', medium: '!', low: '·', info: '✓' },
  coverage: { covered: '✓', partial: '◐', missing: '○', not_applicable: '–' },
} as const;

export const space = [0, 2, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64] as const;

/** Argon rounds generously; the large radius is what reads as "modern" here. */
export const radius = { sm: 6, md: 8, lg: 12, xl: 16, full: 999 } as const;

/**
 * Argon leans on soft, wide, low-opacity shadows rather than borders. Expressed
 * as web box-shadow strings — react-native-web passes `boxShadow` through, and
 * the RN shadow props cannot express a multi-layer shadow at all.
 */
export const shadow = {
  xs: '0 2px 9px -5px rgba(0,0,0,.15)',
  sm: '0 .25rem .375rem -.0625rem rgba(20,20,20,.12), 0 .125rem .25rem -.0625rem rgba(20,20,20,.07)',
  md: '0 .5rem 1rem -.25rem rgba(20,20,20,.12), 0 .25rem .5rem -.125rem rgba(20,20,20,.07)',
  lg: '0 .625rem 1.5rem -.5rem rgba(20,20,20,.16), 0 .375rem .75rem -.25rem rgba(20,20,20,.08)',
} as const;

export const font = {
  sans: '"Open Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  mono: '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace',
  size: { xxs: 10.4, caption: 12, cell: 13, body: 14, lead: 16, h3: 18, h2: 22, h1: 30, hero: 38 },
  weight: { light: '300', regular: '400', medium: '600', bold: '700' },
} as const;
