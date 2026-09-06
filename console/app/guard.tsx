import React from 'react';
import { Text, View } from 'react-native';

import { ExportBar } from '../components/ExportBar';
import {
  Banner, Body, Card, CardHeader, Empty, Hero, KeyValue, Mono, Page, StatCard, styles,
} from '../components/ui';
import { guardMarkdown } from '../lib/export';
import { useLocale } from '../lib/locale';
import { useReport } from '../lib/store';
import { font, radius, semantic, space, useTheme } from '../theme';

export default function Guard() {
  const { state } = useReport();
  const { c } = useTheme();
  const { locale, t } = useLocale();
  const g = state.report.reports.guard;

  if (!g) {
    return (
      <View style={styles.page}>
        <Hero title={t('guard.title')} />
        <Page>
          <Empty title={t('guard.empty')}
            detail={locale === 'tr'
              ? 'LLM istemcinizi GuardedClient ile sarın ve defterini kapıya verin.'
              : 'Wrap your LLM client in GuardedClient and pass its ledger to the gate.'} />
        </Page>
      </View>
    );
  }

  const maskedTotal = Object.values(g.masked_entities).reduce((a, b) => a + b, 0);

  return (
    <View style={styles.page}>
      <Hero
        eyebrow={t('nav.guard')}
        title={t('guard.title')}
        meta={
          <View style={{ flexDirection: 'row', gap: space[4], flexWrap: 'wrap',
            marginTop: space[2] }}>
            <Mono color="rgba(255,255,255,.6)">session {g.session_id}</Mono>
            <Mono color="rgba(255,255,255,.6)">{g.duration_s}s</Mono>
          </View>
        }
      />

      <Page>
        <View style={styles.row}>
          <StatCard label={t('guard.invocations')} value={g.calls} glyph="⇄"
            tone={semantic.info} />
          <StatCard label={t('guard.tokens')} value={g.tokens} glyph="∑" tone={c.accent} />
          <StatCard label={t('guard.blocked')} value={g.blocked_calls} glyph="⨯"
            tone={g.blocked_calls ? semantic.danger : '#8898AA'} />
          <StatCard label={t('guard.degraded')} value={g.degraded_calls} glyph="≈"
            tone={g.degraded_calls ? semantic.degraded : '#8898AA'} />
          <StatCard label={t('guard.entities_masked')} value={maskedTotal} glyph="⚿"
            tone={maskedTotal ? semantic.success : '#8898AA'} />
        </View>

        <Banner tone="info" title={t('guard.no_values.title')}>
          <Body muted>{t('guard.no_values.body')}</Body>
        </Banner>

        {g.degraded_calls ? (
          <Banner tone="degraded" title={`${g.degraded_calls} ${t('common.degraded')}`}>
            <Body muted>
              {locale === 'tr'
                ? 'Model yerine bir yedek yanıt verdi — sağlayıcı hatası, ret, engellenmiş çıktı ya da tükenmiş bütçe. Düşürülmüş yanıtlar asla sessiz değildir: her biri tetikleyicisini taşır ve hiçbiri model yanıtı olarak okunmamalıdır.'
                : 'A fallback answered instead of the model — a provider error, a refusal, a blocked output, or an exhausted budget. Degraded responses are never silent: each one carries its trigger, and none should be read as a model answer.'}
            </Body>
          </Banner>
        ) : null}

        <Card>
          <CardHeader
            title={t('guard.masked_classes')}
            right={<ExportBar kind="guard" subject={g.session_id} json={g}
              markdown={() => guardMarkdown(g, locale, state.source === 'bundled')} />}
          />
          {maskedTotal ? (
            <View style={{ flexDirection: 'row', gap: space[4], flexWrap: 'wrap' }}>
              {Object.entries(g.masked_entities).map(([k, n]) => (
                <View key={k} style={{ paddingHorizontal: space[5], paddingVertical: space[4],
                  borderRadius: radius.lg, backgroundColor: c.surface2, minWidth: 110 }}>
                  <Mono>{k}</Mono>
                  <Text style={{ color: c.accent, fontSize: font.size.h2,
                    fontWeight: font.weight.bold, fontVariant: ['tabular-nums'],
                    fontFamily: font.sans }}>{n}</Text>
                </View>
              ))}
            </View>
          ) : (
            <Body muted>
              {locale === 'tr'
                ? 'Bu oturumda hiçbir şey maskelenmedi. Dedektörler yapısaldır — bir e-posta adresinin biçimi vardır, bir kişinin adının yoktur — bu nedenle bu, tanınabilir hiçbir şey bulunmadığı anlamına gelir, kişisel veri bulunmadığı değil.'
                : "Nothing was masked in this session. The detectors are structural — an email address has a shape, a person's name does not — so this means nothing recognisable was found, never that no personal data was present."}
            </Body>
          )}
        </Card>

        <Card>
          <CardHeader title={t('guard.signatures')} />
          {g.signatures_triggered.length ? (
            <View style={{ gap: space[3] }}>
              {g.signatures_triggered.map((s) => (
                <View key={s} style={{ flexDirection: 'row', gap: space[3], alignItems: 'center' }}>
                  <View style={{ width: 24, height: 24, borderRadius: radius.full,
                    backgroundColor: `${semantic.danger}1F`, alignItems: 'center',
                    justifyContent: 'center' }}>
                    <Text style={{ color: semantic.danger, fontSize: 11,
                      fontFamily: font.mono }}>⨯</Text>
                  </View>
                  <Mono color={c.text} size={font.size.cell}>{s}</Mono>
                </View>
              ))}
            </View>
          ) : (
            <Body muted>
              {locale === 'tr'
                ? 'Bu oturumda hiçbir enjeksiyon veya jailbreak imzası tetiklenmedi.'
                : 'No injection or jailbreak signature fired in this session.'}
            </Body>
          )}
        </Card>

        <Card>
          <CardHeader title={t('guard.governance')} />
          <KeyValue rows={[
            [t('guard.tokens'), g.tokens],
            [t('guard.invocations'), g.calls],
            [locale === 'tr' ? 'Çağrı başına ortalama' : 'Average per call',
              g.calls ? Math.round(g.tokens / g.calls) : 0],
            [locale === 'tr' ? 'Oturum süresi' : 'Session duration', `${g.duration_s}s`],
          ]} />
        </Card>
      </Page>
    </View>
  );
}
