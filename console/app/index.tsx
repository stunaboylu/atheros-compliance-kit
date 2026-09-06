import React from 'react';
import { Text, View } from 'react-native';

import { ExportBar } from '../components/ExportBar';
import {
  Banner, Body, Caption, Card, CardHeader, Empty, Eyebrow, Hero, KeyValue, Mono, Page, Pill,
  ScoreBar, StatCard, styles,
} from '../components/ui';
import { gateMarkdown } from '../lib/export';
import { useLocale } from '../lib/locale';
import { useReport } from '../lib/store';
import { font, radius, semantic, space, useTheme } from '../theme';

const STATUS = {
  pass: { color: semantic.success, glyph: '✓' },
  fail: { color: semantic.danger, glyph: '⨯' },
  unmeasured: { color: semantic.warning, glyph: '?' },
  skipped: { color: '#8898AA', glyph: '–' },
  error: { color: semantic.danger, glyph: '!' },
} as const;

export default function Overview() {
  const { state } = useReport();
  const { c } = useTheme();
  const { locale, t } = useLocale();

  const { report, source, warning } = state;
  const checks = report.checks;
  const skipped = checks.filter((k) => k.status === 'skipped');
  const unmeasured = checks.filter((k) => k.status === 'unmeasured');
  const failed = checks.filter((k) => k.status === 'fail');
  const passed = checks.filter((k) => k.status === 'pass');

  const scores = [
    report.reports.rag?.bias?.fairness_score ?? null,
    report.reports.rag?.quality?.score ?? null,
    report.reports.rag?.drift?.score ?? null,
  ].filter(Boolean);

  return (
    <View style={styles.page}>
      <Hero
        eyebrow={report.schema}
        title={t('gate.title')}
        meta={
          <View style={{ flexDirection: 'row', gap: space[4], alignItems: 'center',
            flexWrap: 'wrap', marginTop: space[2] }}>
            <Pill
              label={report.passed ? t('gate.passed') : t('gate.failed')}
              color={report.passed ? semantic.success : semantic.danger}
              glyph={report.passed ? '✓' : '⨯'}
              solid
            />
            <Mono color="rgba(255,255,255,.6)">session {report.session_id}</Mono>
            <Mono color="rgba(255,255,255,.6)">exit {report.exit_code}</Mono>
          </View>
        }
      />

      <Page>
        <View style={styles.row}>
          <StatCard label={t('stat.passed')} value={passed.length} glyph="✓"
            tone={semantic.success} />
          <StatCard label={t('stat.failed')} value={failed.length} glyph="⨯"
            tone={failed.length ? semantic.danger : '#8898AA'} />
          <StatCard label={t('stat.unmeasured')} value={unmeasured.length} glyph="?"
            tone={unmeasured.length ? semantic.warning : '#8898AA'} />
          <StatCard label={t('stat.skipped')} value={skipped.length} glyph="–"
            tone="#8898AA" />
        </View>

        {source === 'bundled' ? (
          <Banner tone="info" title={t('demo.title')}>
            <Body muted>{t('demo.body')}</Body>
          </Banner>
        ) : null}

        {warning ? (
          <Banner tone="warning" title={t('gate.source')}><Body muted>{warning}</Body></Banner>
        ) : null}

        {unmeasured.length ? (
          <Banner tone="warning" title={t('gate.unmeasured.title')}>
            <Body muted>{unmeasured.length} {t('gate.unmeasured.body')}</Body>
          </Banner>
        ) : null}

        {skipped.length ? (
          <Banner tone="info" title={`${skipped.length} ${t('gate.skipped.title')}`}>
            <Body muted>{t('gate.skipped.body')} {skipped.map((s) => s.name).join(', ')}.</Body>
          </Banner>
        ) : null}

        <Card>
          <CardHeader
            title={t('gate.checks')}
            subtitle={`${checks.length}`}
            right={<ExportBar kind="gate" subject={report.session_id} json={report}
              markdown={() => gateMarkdown(report, locale, source === 'bundled')} />}
          />
          {checks.map((k, i) => {
            const s = STATUS[k.status];
            return (
              <View key={k.name} style={{ flexDirection: 'row', gap: space[4],
                alignItems: 'flex-start', paddingVertical: space[4],
                borderTopWidth: i === 0 ? 0 : 1, borderTopColor: c.border }}>
                <View style={{ width: 26, height: 26, borderRadius: radius.full,
                  alignItems: 'center', justifyContent: 'center',
                  backgroundColor: `${s.color}1F` }}>
                  <Text style={{ color: s.color, fontSize: 12,
                    fontFamily: font.mono }}>{s.glyph}</Text>
                </View>
                <View style={{ flex: 1, gap: space[2] }}>
                  <View style={{ flexDirection: 'row', gap: space[3], alignItems: 'center',
                    flexWrap: 'wrap' }}>
                    <Text style={{ color: c.text, fontSize: font.size.cell,
                      fontWeight: font.weight.medium, fontFamily: font.mono }}>{k.name}</Text>
                    <Pill label={k.status} color={s.color} />
                    {k.actual !== null && k.actual !== undefined ? (
                      <Mono>{String(k.actual)}</Mono>
                    ) : null}
                    {k.threshold !== null && k.threshold !== undefined ? (
                      <Mono>≥ {JSON.stringify(k.threshold)}</Mono>
                    ) : null}
                  </View>
                  {k.detail ? <Caption>{k.detail}</Caption> : null}
                </View>
              </View>
            );
          })}
        </Card>

        {scores.length ? (
          <View style={styles.row}>
            {scores.map((s) => (
              <Card key={s!.name} style={{ flex: 1, minWidth: 280 }}>
                <ScoreBar score={s} />
              </Card>
            ))}
          </View>
        ) : (
          <Empty title={t('common.no_scores')}
            detail={locale === 'tr'
              ? 'Bu çalışma için skor üreten hiçbir modül yapılandırılmadı.'
              : 'No module that produces a score was configured for this run.'} />
        )}

        <Card>
          <CardHeader title={t('gate.run')} />
          <KeyValue rows={[
            [t('gate.result'), report.passed ? t('gate.passed') : `${t('gate.failed')} (${failed.length})`],
            [t('gate.session'), <Mono key="s">{report.session_id}</Mono>],
            [t('gate.schema'), <Mono key="sc">{report.schema}</Mono>],
            [t('gate.artefacts'), <View key="a" style={{ gap: space[1] }}>
              {report.artefacts.map((a) => <Mono key={a}>{a}</Mono>)}
            </View>],
            [t('gate.modules'), <View key="m" style={{ flexDirection: 'row', gap: space[2],
              flexWrap: 'wrap' }}>
              {Object.keys(report.reports).map((m) => (
                <View key={m} style={{ paddingHorizontal: space[3], paddingVertical: 2,
                  borderRadius: radius.sm, backgroundColor: c.surface3 }}>
                  <Mono>{m}</Mono>
                </View>
              ))}
            </View>],
          ]} />
        </Card>
      </Page>
    </View>
  );
}
