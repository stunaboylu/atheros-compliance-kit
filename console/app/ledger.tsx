import React from 'react';
import { Pressable, Text, View } from 'react-native';

import { ExportBar } from '../components/ExportBar';
import {
  Banner, Body, Caption, Card, CardHeader, Hero, Mono, Page, Pill, StatCard, styles,
} from '../components/ui';
import { loadLedger, verifyChain } from '../lib/data';
import { useLocale } from '../lib/locale';
import { font, radius, semantic, space, useTheme } from '../theme';
import type { LedgerEntry } from '../lib/types';

export default function Ledger() {
  const { c } = useTheme();
  const { t } = useLocale();
  const entries = React.useMemo<LedgerEntry[]>(() => loadLedger(), []);
  const [result, setResult] = React.useState<{ intact: boolean; violations: string[] } | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [filter, setFilter] = React.useState<string | null>(null);

  const verify = React.useCallback(async () => {
    setBusy(true);
    try {
      setResult(await verifyChain(entries));
    } finally {
      setBusy(false);
    }
  }, [entries]);

  React.useEffect(() => { verify(); }, [verify]);

  const modules = Array.from(new Set(entries.map((e) => e.module)));
  const shown = filter ? entries.filter((e) => e.module === filter) : entries;

  return (
    <View style={styles.page}>
      <Hero
        eyebrow="ISO/IEC 42001 §9.1"
        title={t('ledger.title')}
        meta={
          <View style={{ flexDirection: 'row', gap: space[4], alignItems: 'center',
            flexWrap: 'wrap', marginTop: space[3] }}>
            {result ? (
              <Pill
                label={result.intact ? t('ledger.intact')
                  : `${result.violations.length} ${t('ledger.violations')}`}
                color={result.intact ? semantic.success : semantic.danger}
                glyph={result.intact ? '✓' : '⨯'}
                solid
              />
            ) : (
              <Pill label={busy ? t('ledger.verifying') : t('ledger.unverified')}
                color={semantic.band.unmeasured} solid />
            )}
            <Mono color="rgba(255,255,255,.6)">
              {entries.length} {t('ledger.entries')}
            </Mono>
          </View>
        }
        right={<ExportBar kind="ledger" subject="audit-trail" json={entries} />}
      />

      <Page>
        <View style={styles.row}>
          <StatCard label={t('ledger.entries')} value={entries.length} glyph="⛓"
            tone={c.accent} />
          {modules.slice(0, 4).map((m) => (
            <StatCard key={m} label={m}
              value={entries.filter((e) => e.module === m).length}
              glyph="▪" tone={semantic.info} />
          ))}
        </View>

        <Card>
          <CardHeader
            title={t('ledger.chain')}
            subtitle={t('ledger.subtitle')}
            right={
              <Pressable
                onPress={verify}
                accessibilityRole="button"
                style={{ paddingHorizontal: space[5], paddingVertical: space[3],
                  borderRadius: radius.md, backgroundColor: c.accentSubtle }}>
                <Text style={{ color: c.accent, fontSize: font.size.caption,
                  fontWeight: font.weight.medium, fontFamily: font.sans }}>
                  {busy ? `${t('ledger.verifying')}…` : t('ledger.reverify')}
                </Text>
              </Pressable>
            }
          />
          <Body muted style={{ fontSize: font.size.cell }}>{t('ledger.independent')}</Body>
          {result && !result.intact ? (
            <View style={{ marginTop: space[5], gap: space[2] }}>
              {result.violations.map((v, i) => <Mono key={i} color={semantic.danger}>{v}</Mono>)}
            </View>
          ) : null}
        </Card>

        {result?.intact ? (
          <Banner tone="success" title={t('ledger.meaning.title')}>
            <Body muted>{t('ledger.meaning.body')}</Body>
          </Banner>
        ) : null}

        <Card>
          <CardHeader
            title={t('ledger.entries')}
            right={
              <View style={{ flexDirection: 'row', gap: space[2], flexWrap: 'wrap' }}>
                <Chip label={t('ledger.all')} active={filter === null}
                  onPress={() => setFilter(null)} />
                {modules.map((m) => (
                  <Chip key={m} label={m} active={filter === m} onPress={() => setFilter(m)} />
                ))}
              </View>
            }
          />
          {shown.map((e, i) => (
            <View key={e.hash} style={{ paddingVertical: space[4],
              borderTopWidth: i === 0 ? 0 : 1, borderTopColor: c.border, gap: space[2] }}>
              <View style={{ flexDirection: 'row', gap: space[3], flexWrap: 'wrap',
                alignItems: 'center' }}>
                <Mono>{e.timestamp.slice(0, 19).replace('T', ' ')}</Mono>
                <View style={{ paddingHorizontal: space[3], paddingVertical: 1,
                  borderRadius: radius.sm, backgroundColor: c.accentSubtle }}>
                  <Mono color={c.accent}>{e.module}</Mono>
                </View>
                <Mono color={c.text}>{e.event_type}</Mono>
              </View>
              <Caption>{e.iso_42001_clause}</Caption>
              <View style={{ flexDirection: 'row', gap: space[4], flexWrap: 'wrap' }}>
                <Mono>hash {e.hash.slice(0, 16)}…</Mono>
                <Mono>prev {e.previous_hash.slice(0, 16)}…</Mono>
              </View>
              <View style={{ backgroundColor: c.surface2, borderRadius: radius.md,
                padding: space[4] }}>
                <Mono>{JSON.stringify(e.payload)}</Mono>
              </View>
            </View>
          ))}
        </Card>
      </Page>
    </View>
  );
}

function Chip({ label, active, onPress }:
  { label: string; active: boolean; onPress: () => void }) {
  const { c } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
      style={{ paddingHorizontal: space[4], paddingVertical: space[2], borderRadius: radius.full,
        backgroundColor: active ? c.accentSubtle : c.surface3 }}>
      <Mono color={active ? c.accent : c.textMuted}>{label}</Mono>
    </Pressable>
  );
}
