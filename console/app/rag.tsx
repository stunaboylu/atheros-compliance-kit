import React from 'react';
import { Text, View } from 'react-native';

import { ExportBar } from '../components/ExportBar';
import {
  Banner, Body, Caption, Card, CardHeader, Empty, Eyebrow, FindingRow, Hero, KeyValue, Limits,
  Mono, Page, Pill, ScoreBar, StatCard, styles,
} from '../components/ui';
import { ragMarkdown } from '../lib/export';
import { useLocale } from '../lib/locale';
import { useReport } from '../lib/store';
import { font, radius, semantic, space, useTheme } from '../theme';

const DRIFT = {
  stable: semantic.success,
  drifting: semantic.warning,
  shifted: semantic.danger,
  unmeasurable: '#8898AA',
} as const;

export default function Rag() {
  const { state } = useReport();
  const { c } = useTheme();
  const { locale, t } = useLocale();
  const rag = state.report.reports.rag;

  if (!rag) {
    return (
      <View style={styles.page}>
        <Hero title={t('nav.rag')} />
        <Page>
          <Empty title={t('rag.empty')}
            detail="atheros-kit rag audit --store chroma --store-config store.json" />
        </Page>
      </View>
    );
  }

  const bias = rag.bias;
  const q = rag.quality;

  return (
    <View style={styles.page}>
      <Hero
        eyebrow={t('nav.rag')}
        title={rag.subject}
        meta={
          <View style={{ flexDirection: 'row', gap: space[4], flexWrap: 'wrap',
            marginTop: space[2] }}>
            <Mono color="rgba(255,255,255,.6)">
              {q.total_chunks} {t('rag.chunks_scanned')}
            </Mono>
            <Mono color="rgba(255,255,255,.6)">session {rag.session_id}</Mono>
          </View>
        }
      />

      <Page>
        <View style={styles.row}>
          <Card style={{ flex: 1, minWidth: 300 }}>
            <Eyebrow>{t('rag.fairness')}</Eyebrow>
            <View style={{ height: space[3] }} />
            <ScoreBar score={bias.fairness_score} label={t('rag.fairness_score')} />
          </Card>
          <Card style={{ flex: 1, minWidth: 300 }}>
            <Eyebrow>{t('rag.quality')}</Eyebrow>
            <View style={{ height: space[3] }} />
            <ScoreBar score={q.score} label={t('rag.quality_score')} />
          </Card>
        </View>

        <View style={styles.row}>
          <StatCard label={t('rag.chunks_scanned')} value={q.total_chunks} glyph="≣"
            tone={semantic.info} />
          <StatCard label="duplicates" value={q.duplicate_chunks} glyph="⧉"
            tone={q.duplicate_chunks ? semantic.warning : '#8898AA'} />
          <StatCard label="unembedded" value={q.orphans} glyph="○"
            tone={q.orphans ? semantic.danger : '#8898AA'} />
          <StatCard label="PII" value={q.pii_chunks} glyph="⚿"
            tone={q.pii_chunks ? semantic.danger : '#8898AA'}
            caption={q.pii_categories.join(', ') || undefined} />
        </View>

        {bias.unassessable.length ? (
          <Banner tone="warning"
            title={`${bias.unassessable.length} ${t('rag.unassessable.title')}`}>
            <Body muted>{bias.unassessable.join(', ')} — {t('rag.unassessable.body')}</Body>
          </Banner>
        ) : null}

        <Card>
          <CardHeader
            title={t('rag.bias_by_dimension')}
            right={<ExportBar kind="rag" subject={rag.subject} json={rag}
              markdown={() => ragMarkdown(rag, locale, state.source === 'bundled')} />}
          />
          {bias.dimensions.map((d, i) => (
            <View key={d.dimension} style={{ paddingVertical: space[5],
              borderTopWidth: i === 0 ? 0 : 1, borderTopColor: c.border, gap: space[3] }}>
              <View style={{ flexDirection: 'row', gap: space[4], alignItems: 'center',
                flexWrap: 'wrap' }}>
                <Text style={{ color: c.text, fontSize: font.size.body,
                  fontWeight: font.weight.medium, fontFamily: font.sans }}>
                  {d.dimension.replace(/_/g, ' ')}
                </Text>
                {d.assessed ? (
                  <>
                    <Pill label={`${d.score?.toFixed(0) ?? '—'} / 100`} color={band(d.score)} />
                    <Mono>rep {d.representation_score?.toFixed(0) ?? '—'}</Mono>
                    <Mono>framing {d.sentiment_score?.toFixed(0) ?? '—'}</Mono>
                    <Mono>{d.total_mentions} mentions</Mono>
                  </>
                ) : (
                  <Pill label={t('rag.unassessable')} color={semantic.band.unmeasured} glyph="?" />
                )}
              </View>

              {!d.assessed ? (
                <Caption>
                  {locale === 'tr' && (d as { reason_tr?: string }).reason_tr
                    ? (d as { reason_tr?: string }).reason_tr : d.reason}
                </Caption>
              ) : (
                <>
                  <View style={{ flexDirection: 'row', gap: space[2], flexWrap: 'wrap' }}>
                    {Object.entries(d.group_counts).map(([g, n]) => {
                      const flagged = d.underrepresented.includes(g)
                        || d.negatively_framed.includes(g);
                      return (
                        <View key={g} style={{ paddingHorizontal: space[4],
                          paddingVertical: space[2], borderRadius: radius.md,
                          backgroundColor: flagged ? `${semantic.warning}14` : c.surface2 }}>
                          <Mono color={flagged ? semantic.warning : c.textMuted}>
                            {g}: {n}{d.negatively_framed.includes(g) ? ' ▼' : ''}
                          </Mono>
                        </View>
                      );
                    })}
                  </View>
                  {d.negatively_framed.length ? (
                    <Caption>▼ {t('rag.negatively_framed')} ({d.sentiment_spread?.toFixed(2)})</Caption>
                  ) : null}
                </>
              )}
            </View>
          ))}
        </Card>

        {rag.drift ? (
          <Card>
            <CardHeader title={t('rag.drift')} right={
              <Pill label={rag.drift.verdict} color={DRIFT[rag.drift.verdict]} solid />} />
            <KeyValue rows={[
              ['Centroid', rag.drift.centroid_informative
                ? String(rag.drift.centroid_similarity)
                : `${rag.drift.centroid_similarity} — excluded (near-isotropic)`],
              ['PSI', `${rag.drift.psi_mean} (threshold ${rag.drift.psi_stable_threshold}, `
                + `sampling floor ${rag.drift.psi_noise_floor})`],
              ['Unstable dimensions', rag.drift.psi_dimensions_unstable],
              ['Volume', `${rag.drift.baseline_count} → ${rag.drift.current_count}`
                + (rag.drift.volume_ratio ? ` (${rag.drift.volume_ratio}×)` : '')],
            ]} />
          </Card>
        ) : (
          <Empty title={t('rag.drift.not_measured')} detail={t('rag.drift.no_baseline')} />
        )}

        <Card>
          <CardHeader title={t('common.findings')} subtitle={`${rag.findings.length}`} />
          {rag.findings.length
            ? rag.findings.map((f, i) => <FindingRow key={f.check + i} finding={f} first={i === 0} />)
            : <Body muted>{t('common.no_findings')}</Body>}
        </Card>

        {rag.remediation?.length ? (
          <Card>
            <CardHeader title={t('common.remediation')} subtitle={t('rag.remediation.note')} />
            {rag.remediation.map((r, i) => (
              <View key={r.key} style={{ paddingVertical: space[4],
                borderTopWidth: i === 0 ? 0 : 1, borderTopColor: c.border, gap: space[2] }}>
                <View style={{ flexDirection: 'row', gap: space[3], alignItems: 'center',
                  flexWrap: 'wrap' }}>
                  <View style={{ width: 24, height: 24, borderRadius: radius.full,
                    backgroundColor: c.accentSubtle, alignItems: 'center',
                    justifyContent: 'center' }}>
                    <Mono color={c.accent}>{i + 1}</Mono>
                  </View>
                  <Text style={{ color: c.text, fontSize: font.size.cell,
                    fontWeight: font.weight.medium, fontFamily: font.sans }}>{r.title}</Text>
                  <Mono>impact {r.impact} · effort {r.effort}</Mono>
                  {r.article ? <Mono color={c.accent}>{r.article}</Mono> : null}
                </View>
                <Body muted style={{ fontSize: font.size.cell }}>{r.rationale}</Body>
                <Caption>Risk: {r.risk}</Caption>
              </View>
            ))}
          </Card>
        ) : null}

        <Limits limits={locale === 'tr' && rag.limits_tr?.length
          ? rag.limits_tr
          : [...rag.limits, ...bias.limits, ...(rag.drift?.limits ?? [])]} />
      </Page>
    </View>
  );
}

function band(v: number | null): string {
  if (v === null) return semantic.band.unmeasured;
  if (v >= 85) return semantic.band.good;
  if (v >= 70) return semantic.band.watch;
  if (v >= 50) return semantic.band.poor;
  return semantic.band.critical;
}
