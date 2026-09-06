/**
 * The component set, in Argon's visual language.
 *
 * Argon's craft is mostly in four things, and each is applied here rather than
 * approximated: soft multi-layer shadows instead of hairline borders; generous
 * radii; Open Sans with a heavier medium weight (600) for labels; and a lot of
 * whitespace inside cards.
 *
 * The two rules from the previous version survive unchanged, because they are
 * about honesty rather than looks:
 *
 * 1. **Never colour alone.** Every state carries a glyph or a word.
 * 2. **Unmeasured is its own state.** `null` renders grey and says so. Never a
 *    zero, never a pass.
 */
import React from 'react';
import { Pressable, StyleSheet, Text, View, ViewStyle } from 'react-native';

import { useLocale } from '../lib/locale';
import { font, glyph, radius, semantic, shadow, space, useTheme } from '../theme';
import type { Action, Band, Coverage, Method, RiskTier, Score, Severity } from '../lib/types';

/** react-native-web passes `boxShadow` through; RN's shadow props cannot express
 *  a two-layer shadow, and Argon's depth comes entirely from layering. */
const elevate = (level: keyof typeof shadow): ViewStyle =>
  ({ boxShadow: shadow[level] } as unknown as ViewStyle);

// ── surfaces ──────────────────────────────────────────────────────────────────
export function Card({ children, style, flush, level = 'sm' }: {
  children: React.ReactNode; style?: ViewStyle; flush?: boolean;
  level?: keyof typeof shadow;
}) {
  const { c } = useTheme();
  return (
    <View style={[{
      backgroundColor: c.surface, borderRadius: radius.lg,
      padding: flush ? 0 : space[8], overflow: 'hidden',
    }, elevate(level), style]}>
      {children}
    </View>
  );
}

export function CardHeader({ title, subtitle, right }: {
  title: string; subtitle?: string; right?: React.ReactNode;
}) {
  const { c } = useTheme();
  return (
    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start',
      gap: space[5], flexWrap: 'wrap', marginBottom: space[5] }}>
      <View style={{ gap: space[1], flexShrink: 1 }}>
        <Text style={{ color: c.text, fontSize: font.size.h3, fontWeight: font.weight.medium,
          fontFamily: font.sans, letterSpacing: -0.2 }}>{title}</Text>
        {subtitle ? (
          <Text style={{ color: c.textFaint, fontSize: font.size.cell, fontFamily: font.sans }}>
            {subtitle}
          </Text>
        ) : null}
      </View>
      {right}
    </View>
  );
}

/** Argon's section label: tiny, uppercase, tracked, muted. */
export function Eyebrow({ children }: { children: React.ReactNode }) {
  const { c } = useTheme();
  return (
    <Text style={{ color: c.textFaint, fontSize: font.size.xxs, fontWeight: font.weight.bold,
      textTransform: 'uppercase', letterSpacing: 1, fontFamily: font.sans }}>
      {children}
    </Text>
  );
}

// ── type ──────────────────────────────────────────────────────────────────────
export function H1({ children, onDark }: { children: React.ReactNode; onDark?: boolean }) {
  const { c } = useTheme();
  return <Text style={{ color: onDark ? '#fff' : c.text, fontSize: font.size.h1,
    fontWeight: font.weight.bold, lineHeight: font.size.h1 * 1.25, letterSpacing: -0.6,
    fontFamily: font.sans }}>{children}</Text>;
}

export function H2({ children }: { children: React.ReactNode }) {
  const { c } = useTheme();
  return <Text style={{ color: c.text, fontSize: font.size.h2, fontWeight: font.weight.medium,
    lineHeight: font.size.h2 * 1.3, letterSpacing: -0.3, marginBottom: space[4],
    fontFamily: font.sans }}>{children}</Text>;
}

export function H3({ children }: { children: React.ReactNode }) {
  const { c } = useTheme();
  return <Text style={{ color: c.text, fontSize: font.size.h3, fontWeight: font.weight.medium,
    marginBottom: space[3], fontFamily: font.sans }}>{children}</Text>;
}

export function Body({ children, muted, onDark, style }: {
  children: React.ReactNode; muted?: boolean; onDark?: boolean; style?: object;
}) {
  const { c } = useTheme();
  const color = onDark ? 'rgba(255,255,255,.82)' : muted ? c.textMuted : c.text;
  return <Text style={[{ color, fontSize: font.size.body, lineHeight: font.size.body * 1.6,
    fontFamily: font.sans }, style]}>{children}</Text>;
}

export function Caption({ children, onDark }: { children: React.ReactNode; onDark?: boolean }) {
  const { c } = useTheme();
  return <Text style={{ color: onDark ? 'rgba(255,255,255,.62)' : c.textFaint,
    fontSize: font.size.caption, lineHeight: font.size.caption * 1.55,
    fontFamily: font.sans }}>{children}</Text>;
}

/** Identifiers, hashes, article numbers and module paths are ALWAYS mono. */
export function Mono({ children, color, size }: {
  children: React.ReactNode; color?: string; size?: number;
}) {
  const { c } = useTheme();
  return <Text style={{ color: color ?? c.textMuted, fontSize: size ?? font.size.caption,
    fontFamily: font.mono }}>{children}</Text>;
}

// ── badges ────────────────────────────────────────────────────────────────────
export function Pill({ label, color, glyph: g, solid }: {
  label: string; color: string; glyph?: string; solid?: boolean;
}) {
  return (
    <View style={{
      flexDirection: 'row', alignItems: 'center', gap: space[2],
      paddingHorizontal: space[4], paddingVertical: space[1] + 2,
      borderRadius: radius.full, alignSelf: 'flex-start',
      backgroundColor: solid ? color : `${color}1F`,
    }}>
      {g ? <Text style={{ color: solid ? '#fff' : color, fontSize: 11,
        fontFamily: font.mono }}>{g}</Text> : null}
      <Text style={{ color: solid ? '#fff' : color, fontSize: 11,
        fontWeight: font.weight.bold, textTransform: 'uppercase', letterSpacing: 0.5,
        fontFamily: font.sans }}>{label}</Text>
    </View>
  );
}

export function RiskBadge({ tier, greyZone, large }: {
  tier: RiskTier; greyZone?: boolean; large?: boolean;
}) {
  const color = semantic.riskTier[tier];
  return (
    <View style={{ flexDirection: 'row', gap: space[3], alignItems: 'center', flexWrap: 'wrap' }}>
      {large ? (
        <View style={{ paddingHorizontal: space[6], paddingVertical: space[3],
          borderRadius: radius.md, backgroundColor: color }}>
          <Text style={{ color: '#fff', fontSize: font.size.lead, fontWeight: font.weight.bold,
            textTransform: 'uppercase', letterSpacing: 1, fontFamily: font.sans }}>{tier}</Text>
        </View>
      ) : <Pill label={tier} color={color} solid />}
      {greyZone ? <Pill label="grey zone" color={semantic.greyZone} glyph="?" /> : null}
    </View>
  );
}

export function ActionPill({ action }: { action: Action }) {
  return <Pill label={action} color={semantic.action[action]} glyph={glyph.action[action]} />;
}

export function SeverityDot({ severity }: { severity: Severity }) {
  const color = semantic.severity[severity];
  return (
    <View style={{ width: 26, height: 26, borderRadius: radius.full, alignItems: 'center',
      justifyContent: 'center', backgroundColor: `${color}1F` }}>
      <Text style={{ color, fontSize: 12, fontFamily: font.mono }}>{glyph.severity[severity]}</Text>
    </View>
  );
}

export function CoverageChip({ value }: { value: Coverage }) {
  return <Pill label={value.replace('_', ' ')} color={semantic.coverage[value]}
    glyph={glyph.coverage[value]} />;
}

export function MethodTag({ method, degraded }: { method: Method; degraded: boolean }) {
  const { c } = useTheme();
  const color = degraded ? semantic.degraded : c.textFaint;
  return (
    <View style={{ paddingHorizontal: space[3], paddingVertical: 2, borderRadius: radius.sm,
      backgroundColor: degraded ? `${semantic.degraded}14` : c.surface3, alignSelf: 'flex-start' }}>
      <Mono color={color}>{method}{degraded ? ' · degraded' : ''}</Mono>
    </View>
  );
}

// ── the Argon stat card ───────────────────────────────────────────────────────
export function StatCard({ label, value, glyph: g, tone, caption }: {
  label: string; value: string | number; glyph: string; tone: string; caption?: string;
}) {
  const { c } = useTheme();
  return (
    <Card style={{ flex: 1, minWidth: 200, padding: space[6] }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between',
        alignItems: 'flex-start', gap: space[4] }}>
        <View style={{ gap: space[1], flexShrink: 1 }}>
          <Eyebrow>{label}</Eyebrow>
          <Text style={{ color: c.text, fontSize: font.size.h1, fontWeight: font.weight.bold,
            fontVariant: ['tabular-nums'], letterSpacing: -0.8, fontFamily: font.sans }}>
            {value}
          </Text>
        </View>
        <View style={[{ width: 44, height: 44, borderRadius: radius.full, backgroundColor: tone,
          alignItems: 'center', justifyContent: 'center' }, elevate('xs')]}>
          <Text style={{ color: '#fff', fontSize: 17, fontFamily: font.mono }}>{g}</Text>
        </View>
      </View>
      {caption ? <View style={{ marginTop: space[3] }}><Caption>{caption}</Caption></View> : null}
    </Card>
  );
}

// ── scores ────────────────────────────────────────────────────────────────────
export function ScoreBar({ score, label }: { score: Score | null; label?: string }) {
  const { c } = useTheme();
  const { t } = useLocale();
  if (!score) return null;
  const band: Band = score.band;
  const color = semantic.band[band];
  const value = score.value;
  const unmeasured = value === null;
  const pct = value === null ? 0 : Math.max(0, Math.min(100, value));

  return (
    <View style={{ gap: space[3] }}>
      <View style={{ flexDirection: 'row', alignItems: 'baseline', gap: space[3], flexWrap: 'wrap' }}>
        <Text style={{ color: unmeasured ? c.textFaint : color, fontSize: font.size.h1,
          fontWeight: font.weight.bold, fontVariant: ['tabular-nums'], letterSpacing: -0.8,
          fontFamily: font.sans }}>
          {unmeasured ? '—' : pct.toFixed(1)}
        </Text>
        <Body muted>{label ?? score.name.replace(/_/g, ' ')}</Body>
        <Pill label={t(`band.${band}` as never)} color={color} />
      </View>

      <View style={{ height: 6, borderRadius: radius.full, backgroundColor: c.surface3,
        overflow: 'hidden' }}>
        {!unmeasured ? (
          <View style={{ width: `${pct}%`, height: '100%', backgroundColor: color,
            borderRadius: radius.full }} />
        ) : (
          <View style={{ width: '100%', height: '100%',
            backgroundColor: `${semantic.band.unmeasured}26` }} />
        )}
      </View>

      <View style={{ flexDirection: 'row', gap: space[4], alignItems: 'center', flexWrap: 'wrap' }}>
        <MethodTag method={score.method} degraded={score.degraded} />
        {score.threshold !== null ? (
          <Caption>
            {t('common.threshold')} {score.threshold}
            {score.passed === null ? ` · ${t('common.unmeasured_does_not_pass')}`
              : score.passed ? ` · ${t('common.pass')}` : ` · ${t('common.fail')}`}
          </Caption>
        ) : null}
      </View>

      {unmeasured ? (
        <Body muted style={{ fontSize: font.size.cell }}>{t('common.unmeasured_note')}</Body>
      ) : null}
    </View>
  );
}

// ── findings ──────────────────────────────────────────────────────────────────
export function FindingRow({ finding, first }: {
  finding: import('../lib/types').Finding; first?: boolean;
}) {
  const { c } = useTheme();
  const { locale, t } = useLocale();
  const [open, setOpen] = React.useState(false);
  const detail = locale === 'tr' && finding.detail_tr ? finding.detail_tr : finding.detail;
  const remediation =
    locale === 'tr' && finding.remediation_tr ? finding.remediation_tr : finding.remediation;

  return (
    <Pressable
      onPress={() => setOpen((v) => !v)}
      accessibilityRole="button"
      accessibilityLabel={`${finding.severity}: ${finding.check}`}
      style={{ borderTopWidth: first ? 0 : 1, borderTopColor: c.border,
        paddingVertical: space[5] }}>
      <View style={{ flexDirection: 'row', gap: space[4], alignItems: 'flex-start' }}>
        <SeverityDot severity={finding.severity} />
        <View style={{ flex: 1, gap: space[2] }}>
          <View style={{ flexDirection: 'row', gap: space[3], alignItems: 'center',
            flexWrap: 'wrap' }}>
            <Text style={{ color: c.text, fontSize: font.size.cell,
              fontWeight: font.weight.medium, fontFamily: font.mono }}>{finding.check}</Text>
            {finding.article ? (
              <View style={{ paddingHorizontal: space[3], paddingVertical: 1,
                borderRadius: radius.sm, backgroundColor: c.accentSubtle }}>
                <Mono color={c.accent}>{finding.article}</Mono>
              </View>
            ) : null}
            <Pill label={t(`severity.${finding.severity}` as never)}
              color={semantic.severity[finding.severity]} />
          </View>
          <Body style={{ fontSize: font.size.cell }}>{detail}</Body>
          {open && remediation ? (
            <View style={{ backgroundColor: c.surface2, borderRadius: radius.md,
              padding: space[5], gap: space[2], marginTop: space[2] }}>
              <Eyebrow>{t('common.remediation')}</Eyebrow>
              <Body style={{ fontSize: font.size.cell }}>{remediation}</Body>
              {Object.keys(finding.evidence).length ? (
                <>
                  <View style={{ height: space[2] }} />
                  <Eyebrow>{t('common.evidence')}</Eyebrow>
                  <Mono>{JSON.stringify(finding.evidence, null, 1)}</Mono>
                </>
              ) : null}
            </View>
          ) : null}
          {!open && remediation ? <Caption>{t('common.tap_remediation')} ›</Caption> : null}
        </View>
      </View>
    </Pressable>
  );
}

export function Limits({ limits }: { limits: string[] }) {
  const { c } = useTheme();
  const { t } = useLocale();
  if (!limits.length) return null;
  return (
    <Card style={{ backgroundColor: c.surface2 }} level="xs">
      <CardHeader title={t('common.limits')} />
      <View style={{ gap: space[4] }}>
        {limits.map((l, i) => (
          <View key={i} style={{ flexDirection: 'row', gap: space[3] }}>
            <Text style={{ color: c.textFaint, fontFamily: font.mono, fontSize: 12,
              marginTop: 3 }}>—</Text>
            <Body muted style={{ flex: 1, fontSize: font.size.cell }}>{l}</Body>
          </View>
        ))}
      </View>
    </Card>
  );
}

export function Banner({ tone, title, children }: {
  tone: 'info' | 'warning' | 'danger' | 'degraded' | 'success';
  title: string; children?: React.ReactNode;
}) {
  const color = { info: semantic.info, warning: semantic.warning, danger: semantic.danger,
    degraded: semantic.degraded, success: semantic.success }[tone];
  const glyphs = { info: 'i', warning: '!', danger: '⨯', degraded: '≈', success: '✓' };
  return (
    <View style={[{ flexDirection: 'row', gap: space[4], backgroundColor: `${color}12`,
      padding: space[5], borderRadius: radius.lg, alignItems: 'flex-start' }]}>
      <View style={{ width: 26, height: 26, borderRadius: radius.full, backgroundColor: color,
        alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ color: '#fff', fontSize: 12, fontWeight: font.weight.bold,
          fontFamily: font.mono }}>{glyphs[tone]}</Text>
      </View>
      <View style={{ flex: 1, gap: space[2] }}>
        <Text style={{ color, fontWeight: font.weight.bold, fontSize: font.size.cell,
          fontFamily: font.sans }}>{title}</Text>
        {children}
      </View>
    </View>
  );
}

export function KeyValue({ rows }: { rows: Array<[string, React.ReactNode]> }) {
  const { c } = useTheme();
  return (
    <View>
      {rows.map(([k, v], i) => (
        <View key={`${k}-${i}`} style={{ flexDirection: 'row', gap: space[5],
          paddingVertical: space[4], borderTopWidth: i === 0 ? 0 : 1, borderTopColor: c.border,
          alignItems: 'flex-start' }}>
          <View style={{ width: 180 }}>
            <Text style={{ color: c.textFaint, fontSize: font.size.cell,
              fontFamily: font.sans }}>{k}</Text>
          </View>
          <View style={{ flex: 1 }}>
            {typeof v === 'string' || typeof v === 'number'
              ? <Body style={{ fontSize: font.size.cell }}>{v}</Body> : v}
          </View>
        </View>
      ))}
    </View>
  );
}

export function Empty({ title, detail }: { title: string; detail: string }) {
  return (
    <Card>
      <H3>{title}</H3>
      <Body muted>{detail}</Body>
    </Card>
  );
}

/** Argon's dark gradient hero. Every screen opens with one. */
export function Hero({ eyebrow, title, meta, right, children }: {
  eyebrow?: string; title: string; meta?: React.ReactNode; right?: React.ReactNode;
  children?: React.ReactNode;
}) {
  const { c } = useTheme();
  return (
    <View style={[{
      backgroundColor: c.gradientFrom,
      backgroundImage: `linear-gradient(87deg, ${c.gradientFrom} 0%, ${c.gradientTo} 100%)`,
      paddingTop: space[9], paddingBottom: space[11], paddingHorizontal: space[7],
    } as unknown as ViewStyle]}>
      <View style={{ maxWidth: 1160, width: '100%', alignSelf: 'center', gap: space[4] }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between',
          alignItems: 'flex-start', gap: space[6], flexWrap: 'wrap' }}>
          <View style={{ gap: space[2], flexShrink: 1 }}>
            {eyebrow ? (
              <Text style={{ color: 'rgba(255,255,255,.55)', fontSize: font.size.xxs,
                fontWeight: font.weight.bold, textTransform: 'uppercase', letterSpacing: 1.2,
                fontFamily: font.sans }}>{eyebrow}</Text>
            ) : null}
            <H1 onDark>{title}</H1>
            {meta}
          </View>
          {right}
        </View>
        {children}
      </View>
    </View>
  );
}

/** Cards that overlap the hero — Argon's signature dashboard move. */
export function Page({ children }: { children: React.ReactNode }) {
  return (
    <View style={{ maxWidth: 1160, width: '100%', alignSelf: 'center',
      paddingHorizontal: space[7], paddingBottom: space[10], marginTop: -space[9], gap: space[6] }}>
      {children}
    </View>
  );
}

export const styles = StyleSheet.create({
  page: { paddingBottom: space[10] },
  row: { flexDirection: 'row', gap: space[6], flexWrap: 'wrap' },
});
