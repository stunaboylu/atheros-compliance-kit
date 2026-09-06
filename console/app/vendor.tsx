import React from 'react';
import { Text, View } from 'react-native';

import { ExportBar } from '../components/ExportBar';
import {
  Banner, Body, Caption, Card, CardHeader, Empty, FindingRow, Hero, KeyValue, Limits, Mono, Page,
  Pill, ScoreBar, styles,
} from '../components/ui';
import { Locale, t } from '../lib/i18n';
import { vendorMarkdown } from '../lib/export';
import { useLocale } from '../lib/locale';
import { useReport } from '../lib/store';
import { font, radius, semantic, space, useTheme } from '../theme';

const RESIDENCY = {
  compliant: semantic.success,
  requires_scc: semantic.warning,
  non_compliant: semantic.danger,
  unknown: semantic.band.unmeasured,
} as const;

const OPTOUT = {
  enforced: semantic.success,
  available_not_evidenced: semantic.warning,
  not_available: semantic.danger,
  unknown: semantic.band.unmeasured,
} as const;

const STATUS = {
  met: { color: semantic.success, glyph: '✓' },
  partial: { color: semantic.warning, glyph: '◐' },
  not_met: { color: semantic.danger, glyph: '⨯' },
  unknown: { color: semantic.band.unmeasured, glyph: '?' },
} as const;

export default function Vendor() {
  const { state } = useReport();
  const { c } = useTheme();
  const { locale, t: tr } = useLocale();
  const vendors = state.report.reports.vendor;

  if (!vendors?.length) {
    return (
      <View style={styles.page}>
        <Hero title={tr('nav.vendor')} />
        <Page>
          <Empty title={tr('vendor.empty')}
            detail="atheros-kit vendor assess openai --region EU" />
        </Page>
      </View>
    );
  }

  return (
    <View style={styles.page}>
      <Hero
        eyebrow={tr('nav.vendor')}
        title={tr('nav.vendor')}
        meta={<Mono color="rgba(255,255,255,.6)">
          {vendors.length} {locale === 'tr' ? 'satıcı' : 'providers'}
        </Mono>}
        right={<ExportBar
          kind="vendor"
          subject={vendors.length === 1 ? vendors[0].provider : 'providers'}
          json={vendors}
          markdown={() => vendorMarkdown(vendors, locale, state.source === 'bundled')}
        />}
      />

      <Page>
        {vendors.map((v) => (
          <View key={v.provider} style={{ gap: space[6] }}>
            <Card>
              <CardHeader
                title={v.provider}
                subtitle={`${locale === 'tr' ? 'bilgi tarihi' : 'facts as of'} ${v.as_of}`}
                right={
                  <View style={{ flexDirection: 'row', gap: space[2], flexWrap: 'wrap' }}>
                    <Pill label={v.residency.verdict.replace(/_/g, ' ')}
                      color={RESIDENCY[v.residency.verdict]} solid />
                    <Pill label={v.training_optout.verdict.replace(/_/g, ' ')}
                      color={OPTOUT[v.training_optout.verdict]} solid />
                  </View>
                }
              />
              <ScoreBar score={v.scores.find((s) => s.name === 'vendor_score') ?? null}
                label={tr('vendor.score')} />

              <View style={{ marginTop: space[7], gap: space[4] }}>
                {Object.entries(v.group_scores).map(([g, s]) => (
                  <View key={g} style={{ gap: space[2] }}>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                      <Body style={{ fontSize: font.size.cell }}>{g.replace(/_/g, ' ')}</Body>
                      <Mono color={c.text}>{s.toFixed(0)}</Mono>
                    </View>
                    <View style={{ height: 5, borderRadius: radius.full,
                      backgroundColor: c.surface3 }}>
                      <View style={{ width: `${Math.max(0, Math.min(100, s))}%`, height: '100%',
                        borderRadius: radius.full,
                        backgroundColor: s >= 80 ? semantic.success
                          : s >= 50 ? semantic.warning : semantic.danger }} />
                    </View>
                  </View>
                ))}
              </View>
            </Card>

            {v.stale ? (
              <Banner tone="warning" title={locale === 'tr'
                ? `${v.as_of} tarihli bilgiler tazelik penceresini aşmış`
                : `Facts dated ${v.as_of} are past the freshness window`}>
                <Body muted>
                  {locale === 'tr'
                    ? 'Satıcı koşulları haber verilmeksizin değişir. Yeniden doğrulayın ve kendi yanıtlarınızı `overrides=` ile geçirin — güncel tarihi olmayan bir bilgi bir söylentidir.'
                    : 'Vendor terms change without notice. Re-verify and pass your own answers via `overrides=` — a fact without a recent date is a rumour.'}
                </Body>
              </Banner>
            ) : null}

            {!v.customer_verified ? (
              <Banner tone="info" title={locale === 'tr'
                ? 'Müşteri tarafından doğrulanmamış' : 'Not customer-verified'}>
                <Body muted>
                  {locale === 'tr'
                    ? 'Bu, bir satıcının neyi sunduğunu tarif eden kamuya açık dokümantasyonu yansıtır — hesabınızda neyin yapılandırıldığını ya da sözleşmenizde neyin yazdığını değil.'
                    : 'This reflects public documentation, which describes what a vendor offers — not what is configured on your account or written into your contract.'}
                </Body>
              </Banner>
            ) : null}

            <View style={styles.row}>
              <Card style={{ flex: 1, minWidth: 300 }}>
                <CardHeader title={tr('vendor.residency')} />
                <KeyValue rows={[
                  [locale === 'tr' ? 'İşleme bölgeleri' : 'Processing regions',
                    v.residency.processing_regions.join(', ')
                      || (locale === 'tr' ? 'kayıtlı değil' : 'not recorded')],
                  [locale === 'tr' ? 'Gerekli bölgeler' : 'Required regions',
                    v.residency.required_regions.join(', ')],
                  [locale === 'tr' ? 'Gerekli dışı' : 'Outside required',
                    v.residency.outside_required.join(', ') || '—'],
                  [locale === 'tr' ? 'Aktarım mekanizması' : 'Transfer mechanism',
                    v.residency.mechanism],
                ]} />
                {v.residency.notes.map((n, i) => <Caption key={i}>{n}</Caption>)}
              </Card>

              <Card style={{ flex: 1, minWidth: 300 }}>
                <CardHeader title={tr('vendor.optout')} subtitle={tr('vendor.optout.note')} />
                <KeyValue rows={[
                  [tr('vendor.available'), tri(v.training_optout.available, locale)],
                  [tr('vendor.enabled'), tri(v.training_optout.enabled, locale)],
                  [tr('vendor.contractual'), tri(v.training_optout.contractual, locale)],
                  [tr('vendor.zdr'), tri(v.training_optout.zdr_enabled, locale)],
                ]} />
              </Card>
            </View>

            <Card>
              <CardHeader title={tr('vendor.criteria')}
                subtitle={`${v.unknown_criteria.length} / 24 ${tr('vendor.not_established')}`} />
              <View style={{ flexDirection: 'row', gap: space[2], flexWrap: 'wrap' }}>
                {Object.entries(v.statuses).map(([k, s]) => (
                  <View key={k} style={{ flexDirection: 'row', alignItems: 'center',
                    gap: space[2], paddingHorizontal: space[4], paddingVertical: space[2] + 1,
                    borderRadius: radius.md, backgroundColor: `${STATUS[s].color}14` }}>
                    <Text style={{ color: STATUS[s].color, fontFamily: font.mono, fontSize: 11 }}>
                      {STATUS[s].glyph}
                    </Text>
                    <Mono color={STATUS[s].color}>{k}</Mono>
                  </View>
                ))}
              </View>
            </Card>

            <Card>
              <CardHeader title={tr('common.findings')} subtitle={`${v.findings.length}`} />
              {v.findings.map((f, i) => (
                <FindingRow key={f.check + i} finding={f} first={i === 0} />
              ))}
            </Card>

            <Limits limits={locale === 'tr' && v.limits_tr?.length ? v.limits_tr : v.limits} />
          </View>
        ))}
      </Page>
    </View>
  );
}

function tri(v: boolean | null, locale: Locale): React.ReactNode {
  if (v === true) return <Pill label={t('vendor.yes', locale)} color={semantic.success} glyph="✓" />;
  if (v === false) return <Pill label={t('vendor.no', locale)} color={semantic.danger} glyph="⨯" />;
  return (
    <Pill label={t('vendor.not_established', locale)} color={semantic.band.unmeasured} glyph="?" />
  );
}
