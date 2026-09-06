import React from 'react';
import { Text, View } from 'react-native';

import { ExportBar } from '../components/ExportBar';
import {
  Banner, Body, Caption, Card, CardHeader, Empty, Hero, KeyValue, Limits, Mono, Page, RiskBadge,
  styles,
} from '../components/ui';
import { riskMarkdown } from '../lib/export';
import { useLocale } from '../lib/locale';
import { useReport } from '../lib/store';
import { font, radius, semantic, space, useTheme } from '../theme';

export default function Risk() {
  const { state } = useReport();
  const { c } = useTheme();
  const { locale, t } = useLocale();
  const cls = state.report.reports.euact;

  if (!cls) {
    return (
      <View style={styles.page}>
        <Hero title={t('nav.risk')} />
        <Page><Empty title={t('risk.empty')} detail={t('risk.empty.detail')} /></Page>
      </View>
    );
  }

  const reasoning = locale === 'tr' && cls.reasoning_tr?.length ? cls.reasoning_tr : cls.reasoning;
  const limits = locale === 'tr' && cls.limits_tr?.length ? cls.limits_tr : cls.limits;
  const grey = locale === 'tr' && cls.grey_zone_reason_tr
    ? cls.grey_zone_reason_tr : cls.grey_zone_reason;

  return (
    <View style={styles.page}>
      <Hero
        eyebrow={cls.regulation_version}
        title={cls.system}
        meta={
          <View style={{ flexDirection: 'row', gap: space[4], alignItems: 'center',
            flexWrap: 'wrap', marginTop: space[3] }}>
            <RiskBadge tier={cls.tier} greyZone={cls.grey_zone} large />
            <Mono color="rgba(255,255,255,.6)">
              {t('risk.confidence')} {cls.confidence.toFixed(2)}
            </Mono>
            <Mono color="rgba(255,255,255,.6)">{t('risk.basis')}: {cls.evidence_basis}</Mono>
          </View>
        }
      />

      <Page>
        {cls.grey_zone ? (
          <Banner tone="degraded" title={t('risk.grey.title')}><Body muted>{grey}</Body></Banner>
        ) : null}

        {cls.evidence_basis === 'no_indicator_matched' ? (
          <Banner tone="warning" title={t('risk.no_indicator.title')}>
            <Body muted>{t('risk.no_indicator.body')}</Body>
          </Banner>
        ) : null}

        {cls.evidence_basis === 'sector_only' ? (
          <Banner tone="warning" title={t('risk.sector_only.title')}>
            <Body muted>{t('risk.sector_only.body')}</Body>
          </Banner>
        ) : null}

        <Card>
          <CardHeader
            title={t('risk.reasoning')}
            right={<ExportBar kind="risk" subject={cls.system} json={cls}
              markdown={() => riskMarkdown(cls, locale, state.source === 'bundled')} />}
          />
          <View style={{ gap: space[3] }}>
            {reasoning.map((r, i) => (
              <View key={i} style={{ flexDirection: 'row', gap: space[3] }}>
                <Text style={{ color: c.accent, fontFamily: font.mono, fontSize: 12,
                  marginTop: 3 }}>▸</Text>
                <Body style={{ flex: 1, fontSize: font.size.cell }}>{r}</Body>
              </View>
            ))}
          </View>
          <View style={{ marginTop: space[6] }}>
            <KeyValue rows={[
              [t('risk.articles'), <View key="a" style={{ flexDirection: 'row', gap: space[2],
                flexWrap: 'wrap' }}>
                {cls.articles.map((a) => (
                  <View key={a} style={{ paddingHorizontal: space[3], paddingVertical: 2,
                    borderRadius: radius.sm, backgroundColor: c.accentSubtle }}>
                    <Mono color={c.accent}>{a}</Mono>
                  </View>
                ))}
              </View>],
              [t('risk.annex'), cls.annex_categories.join(', ') || '—'],
            ]} />
          </View>
        </Card>

        <Card>
          <CardHeader title={t('risk.obligations')} subtitle={t('risk.obligations.note')} />
          {cls.obligations.map((o, i) => (
            <View key={`${o.article}-${i}`} style={{ paddingVertical: space[4],
              borderTopWidth: i === 0 ? 0 : 1, borderTopColor: c.border, gap: space[2] }}>
              <View style={{ flexDirection: 'row', gap: space[3], alignItems: 'center',
                flexWrap: 'wrap' }}>
                <View style={{ paddingHorizontal: space[3], paddingVertical: 2,
                  borderRadius: radius.sm, backgroundColor: c.accentSubtle }}>
                  <Mono color={c.accent}>{o.article}</Mono>
                </View>
                <Mono color={o.evidence_source === '—' ? c.textFaint : semantic.success}>
                  {o.evidence_source === '—'
                    ? t('risk.no_module') : `${t('risk.evidence_by')}: ${o.evidence_source}`}
                </Mono>
              </View>
              <Body style={{ fontSize: font.size.cell }}>
                {locale === 'tr' && o.duty_tr ? o.duty_tr : o.duty}
              </Body>
              {o.note ? <Caption>{o.note}</Caption> : null}
            </View>
          ))}
        </Card>

        {cls.gpai_obligations.length ? (
          <Card>
            <CardHeader title={t('risk.gpai')} subtitle={t('risk.gpai.note')} />
            {cls.gpai_obligations.map((o, i) => (
              <View key={o.article} style={{ paddingVertical: space[3],
                borderTopWidth: i === 0 ? 0 : 1, borderTopColor: c.border, gap: space[1] }}>
                <Mono color={c.accent}>{o.article}</Mono>
                <Body style={{ fontSize: font.size.cell }}>
                  {locale === 'tr' && o.duty_tr ? o.duty_tr : o.duty}
                </Body>
              </View>
            ))}
          </Card>
        ) : null}

        <Limits limits={limits} />
        <Caption>{t('risk.footer')}</Caption>
      </Page>
    </View>
  );
}
