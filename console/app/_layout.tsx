import { Slot, usePathname, useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { Pressable, ScrollView, Text, useWindowDimensions, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { Key } from '../lib/i18n';
import { LocaleProvider, useLocale } from '../lib/locale';
import { ReportProvider } from '../lib/store';
import { font, radius, shadow, space, ThemeProvider, useTheme } from '../theme';

const NAV: Array<{ href: string; key: Key; glyph: string }> = [
  { href: '/', key: 'nav.overview', glyph: '◈' },
  { href: '/risk', key: 'nav.risk', glyph: '⚖' },
  { href: '/rag', key: 'nav.rag', glyph: '≣' },
  { href: '/guard', key: 'nav.guard', glyph: '⛨' },
  { href: '/vendor', key: 'nav.vendor', glyph: '⌂' },
  { href: '/ledger', key: 'nav.ledger', glyph: '⛓' },
];

/**
 * Print rules, injected once on web.
 *
 * The browser's own "Save as PDF" is the export path: no library, no server, no
 * font embedding. What it needs from us is a page that drops the chrome, does
 * not clip inside scroll containers, and keeps its colours — a printed
 * compliance page whose severity colours turned grey is a page whose severities
 * are gone.
 */
const PRINT_CSS = `
@media print {
  [data-print='hide'], .no-print { display: none !important; }
  html, body, #root { height: auto !important; overflow: visible !important;
    background: #fff !important; }
  * { box-shadow: none !important; -webkit-print-color-adjust: exact;
      print-color-adjust: exact; }
  div[style*="overflow"] { overflow: visible !important; }
  @page { margin: 14mm 12mm 16mm; }
}
`;

function usePrintStyles() {
  React.useEffect(() => {
    if (typeof document === 'undefined') return;
    if (document.getElementById('atheros-print')) return;
    const el = document.createElement('style');
    el.id = 'atheros-print';
    el.textContent = PRINT_CSS;
    document.head.appendChild(el);
  }, []);
}

/**
 * Marks a subtree the print stylesheet drops.
 *
 * `dataSet` is react-native-web's escape hatch to a DOM `data-` attribute and is
 * absent from React Native's own ViewProps, so the cast lives here once rather
 * than as a suppression comment at every call site.
 */
function NoPrint({ children }: { children: React.ReactNode }) {
  const props = { dataSet: { print: 'hide' } } as unknown as React.ComponentProps<typeof View>;
  return <View {...props}>{children}</View>;
}

const SIDEBAR = 248;
/** Below this the sidebar becomes a scrolling tab strip. Argon's own breakpoint. */
const WIDE = 1100;

function Sidebar({ wide }: { wide: boolean }) {
  const { c } = useTheme();
  const { t } = useLocale();
  const path = usePathname();
  const router = useRouter();

  const item = (n: (typeof NAV)[number]) => {
    const active = path === n.href;
    return (
      <Pressable
        key={n.href}
        onPress={() => router.push(n.href as never)}
        accessibilityRole="link"
        accessibilityState={{ selected: active }}
        style={{
          flexDirection: 'row', alignItems: 'center', gap: space[4],
          paddingHorizontal: space[5], paddingVertical: space[4],
          borderRadius: radius.md,
          backgroundColor: active ? c.accentSubtle : 'transparent',
        }}>
        <View style={{ width: 30, height: 30, borderRadius: radius.md,
          alignItems: 'center', justifyContent: 'center',
          backgroundColor: active ? c.accent : c.surface3 }}>
          <Text style={{ color: active ? '#fff' : c.textFaint, fontSize: 14,
            fontFamily: font.mono }}>{n.glyph}</Text>
        </View>
        <Text numberOfLines={1} style={{
          color: active ? c.accent : c.textMuted, fontSize: font.size.cell,
          fontWeight: active ? font.weight.medium : font.weight.regular, fontFamily: font.sans,
        }}>{t(n.key)}</Text>
      </Pressable>
    );
  };

  if (!wide) {
    return (
      <ScrollView horizontal showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ gap: space[2], paddingHorizontal: space[5],
          paddingVertical: space[3] }}
        style={{ backgroundColor: c.surface, borderBottomWidth: 1, borderBottomColor: c.border }}>
        {NAV.map(item)}
      </ScrollView>
    );
  }

  return (
    <View style={[{
      width: SIDEBAR, backgroundColor: c.surface, paddingHorizontal: space[4],
      paddingVertical: space[6], gap: space[6], borderTopRightRadius: radius.xl,
      borderBottomRightRadius: radius.xl,
    }, { boxShadow: shadow.sm } as never]}>
      <View style={{ paddingHorizontal: space[4], gap: space[1] }}>
        <Text style={{ color: c.text, fontSize: font.size.lead, fontWeight: font.weight.bold,
          letterSpacing: -0.3, fontFamily: font.sans }}>AtherosAI</Text>
        <Text style={{ color: c.textFaint, fontSize: font.size.caption,
          fontFamily: font.sans }}>Compliance Kit</Text>
      </View>
      <View style={{ height: 1, backgroundColor: c.border }} />
      <View style={{ gap: space[1] }}>{NAV.map(item)}</View>
    </View>
  );
}

function Topbar() {
  const { c, mode, setMode } = useTheme();
  const { locale, setLocale, t } = useLocale();
  const path = usePathname();
  const current = NAV.find((n) => n.href === path);

  const control = (label: string, onPress: () => void, primary?: boolean) => (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={label}
      style={{
        paddingHorizontal: space[4], paddingVertical: space[2] + 1, borderRadius: radius.md,
        backgroundColor: primary ? c.accentSubtle : c.surface3,
      }}>
      <Text style={{ color: primary ? c.accent : c.textMuted, fontSize: font.size.caption,
        fontWeight: font.weight.medium, fontFamily: font.mono }}>{label}</Text>
    </Pressable>
  );

  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
      gap: space[5], paddingHorizontal: space[7], paddingVertical: space[5], flexWrap: 'wrap' }}>
      <View style={{ gap: space[1] }}>
        <Text style={{ color: 'rgba(255,255,255,.55)', fontSize: font.size.xxs,
          fontFamily: font.mono }}>
          atheros / {current ? t(current.key).toLowerCase() : '—'}
        </Text>
        <Text style={{ color: '#fff', fontSize: font.size.cell, fontWeight: font.weight.medium,
          fontFamily: font.sans }}>{t('app.title')}</Text>
      </View>
      <View style={{ flexDirection: 'row', gap: space[2] }}>
        {control(locale === 'en' ? 'TR' : 'EN', () => setLocale(locale === 'en' ? 'tr' : 'en'), true)}
        {control(mode, () => setMode(mode === 'dark' ? 'light' : mode === 'light' ? 'system' : 'dark'))}
      </View>
    </View>
  );
}

function Chrome({ children }: { children: React.ReactNode }) {
  const { c } = useTheme();
  const { t } = useLocale();
  const { width } = useWindowDimensions();
  const wide = width >= WIDE;
  usePrintStyles();

  return (
    <View style={{ flex: 1, backgroundColor: c.bg, flexDirection: wide ? 'row' : 'column' }}>
      <StatusBar style="light" />
      <NoPrint>
        <Sidebar wide={wide} />
      </NoPrint>
      <ScrollView style={{ flex: 1 }} contentContainerStyle={{ flexGrow: 1 }}>
        {/* The topbar sits ON the gradient hero, which each screen renders. */}
        <View style={{ backgroundColor: c.gradientFrom, backgroundImage:
          `linear-gradient(87deg, ${c.gradientFrom} 0%, ${c.gradientTo} 100%)` } as never}>
          <NoPrint>
            <View style={{ maxWidth: 1160, width: '100%', alignSelf: 'center' }}>
              <Topbar />
            </View>
          </NoPrint>
        </View>
        {children}
        <View style={{ paddingHorizontal: space[7], paddingBottom: space[8],
          maxWidth: 1160, width: '100%', alignSelf: 'center' }}>
          <Text style={{ color: c.textFaint, fontSize: font.size.caption, lineHeight: 18,
            fontFamily: font.sans }}>
            {t('gate.footer')}
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <LocaleProvider>
          <ReportProvider>
            <Chrome>
              <Slot />
            </Chrome>
          </ReportProvider>
        </LocaleProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
