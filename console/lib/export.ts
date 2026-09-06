/**
 * Downloads, without a server.
 *
 * Everything here runs in the viewer's browser against data already in memory —
 * the Console has no backend to ask, and adding one to produce a PDF would
 * undo the property the whole product is sold on.
 *
 * Two rules every exported file follows:
 *
 * 1. **A sample export says it is a sample, in the file itself.** Someone will
 *    export the public demo and forward it. A document that reads like a real
 *    assessment because the banner was only on the web page is precisely the
 *    false-assurance failure this product exists to prevent.
 * 2. **The non-certification footer travels with the file.** It is part of the
 *    assessment, not decoration on the page it was read from.
 */
import { Platform } from 'react-native';

import { Locale, t } from './i18n';
import type { Classification, GateReport, GuardSummary, RagReport, Report, VendorReport } from './types';

const isWeb = Platform.OS === 'web';

/** Downloads are a web affordance; on a phone the buttons are not rendered. */
export const canExport = isWeb;

function save(content: string, filename: string, mime: string): void {
  if (!isWeb) return;
  const blob = new Blob([content], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Revoke on the next tick rather than immediately: Safari has not finished
  // reading the blob when click() returns, and an early revoke yields an empty file.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function downloadJSON(data: unknown, filename: string): void {
  save(JSON.stringify(data, null, 2), filename, 'application/json');
}

export function downloadMarkdown(text: string, filename: string): void {
  save(text, filename, 'text/markdown');
}

export function printPage(): void {
  if (isWeb) window.print();
}

/** `atheros-risk-talentflow-2026-09-06.md` — sortable, and says what it is. */
export function filename(kind: string, subject: string, ext: string): string {
  const slug = subject.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'report';
  const day = new Date().toISOString().slice(0, 10);
  return `atheros-${kind}-${slug}-${day}.${ext}`;
}

// ── Markdown renderers ────────────────────────────────────────────────────────
// These mirror what the Python toolkit writes, so a file exported from the
// Console and one written by `atheros-kit` are the same document. If they drift,
// two people reading "the report" are reading different things.

const FOOTER: Record<Locale, string> = {
  en: '_Automated assessment by the AtherosAI Developer Compliance Kit. It evidences what was '
    + 'measured and names what was not. It is not a certification and not a legal opinion._',
  tr: '_AtherosAI Developer Compliance Kit tarafından üretilen otomatik değerlendirme. Ölçülen '
    + 'şeyi kanıtlar ve ölçülmeyeni açıkça belirtir. Belgelendirme değildir ve hukuki görüş '
    + 'niteliği taşımaz._',
};

const SAMPLE: Record<Locale, string> = {
  en: '> ⚠️ **SAMPLE DATA — NOTHING IN THIS DOCUMENT IS REAL.** It was produced from a synthetic '
    + 'corpus and an invented system for demonstration. Do not file, forward, or cite it as an '
    + 'assessment of any actual system.',
  tr: '> ⚠️ **ÖRNEK VERİ — BU BELGEDEKİ HİÇBİR ŞEY GERÇEK DEĞİL.** Gösterim amacıyla sentetik bir '
    + 'külliyat ve uydurma bir sistemden üretilmiştir. Gerçek bir sistemin değerlendirmesi olarak '
    + 'dosyalamayın, iletmeyin veya atıf yapmayın.',
};

function head(title: string, locale: Locale, sample: boolean, meta: string[]): string[] {
  const lines = [`# ${title}`, ''];
  if (sample) lines.push(SAMPLE[locale], '');
  lines.push(`_${meta.join(' · ')}_`, '');
  return lines;
}

function detail(f: { detail: string; detail_tr?: string }, locale: Locale): string {
  return (locale === 'tr' && f.detail_tr ? f.detail_tr : f.detail).replace(/\|/g, '\\|');
}

function findingsTable(report: Report, locale: Locale): string[] {
  if (!report.findings.length) return ['', t('common.no_findings', locale)];
  const head_ = locale === 'tr'
    ? '| Önem | Kontrol | Madde | Ayrıntı |' : '| Severity | Check | Article | Detail |';
  return [
    '', `## ${t('common.findings', locale)}`, '', head_, '|---|---|---|---|',
    ...[...report.findings]
      .sort((a, b) => rank(b.severity) - rank(a.severity))
      .map((f) => `| ${t(`severity.${f.severity}` as never, locale)} | \`${f.check}\` | `
        + `${f.article ?? '—'} | ${detail(f, locale)} |`),
  ];
}

function rank(s: string): number {
  return { critical: 4, high: 3, medium: 2, low: 1, info: 0 }[s] ?? 0;
}

function scoresTable(report: Report, locale: Locale): string[] {
  if (!report.scores.length) return [];
  const head_ = locale === 'tr'
    ? '| Skor | Değer | Bant | Yöntem | Eşik |' : '| Score | Value | Band | Method | Threshold |';
  return [
    '', `## ${t('common.scores', locale)}`, '', head_, '|---|---:|---|---|---:|',
    ...report.scores.map((s) => `| ${s.name} | ${s.value === null ? '—' : s.value.toFixed(1)} | `
      + `${t(`band.${s.band}` as never, locale)} | \`${s.method}\` | ${s.threshold ?? '—'} |`),
  ];
}

function limitsList(report: Report, locale: Locale): string[] {
  const limits = locale === 'tr' && report.limits_tr?.length ? report.limits_tr : report.limits;
  if (!limits.length) return [];
  return ['', `## ${t('common.limits', locale)}`, '', ...limits.map((l) => `- ${l}`)];
}

export function gateMarkdown(report: GateReport, locale: Locale, sample: boolean): string {
  const head_ = locale === 'tr'
    ? '| | Kontrol | Değer | Eşik | Ayrıntı |' : '| | Check | Actual | Threshold | Detail |';
  const icon: Record<string, string> = {
    pass: '✅', fail: '❌', unmeasured: '⚠️', skipped: '⏭️', error: '💥',
  };
  const skipped = report.checks.filter((c) => c.status === 'skipped');
  const lines = [
    ...head(`${t('gate.title', locale)} — ${report.passed ? t('gate.passed', locale) : t('gate.failed', locale)}`,
      locale, sample, [`session ${report.session_id}`, `exit ${report.exit_code}`, report.schema]),
    head_, '|---|---|---|---|---|',
    ...report.checks.map((c) => `| ${icon[c.status] ?? '·'} | \`${c.name}\` | `
      + `${c.actual ?? '—'} | ${c.threshold === null || c.threshold === undefined ? '—' : JSON.stringify(c.threshold)} | ${c.detail} |`),
  ];
  if (skipped.length) {
    lines.push('', `> **${skipped.length} ${t('gate.skipped.title', locale)}.** `
      + `${t('gate.skipped.body', locale)} ${skipped.map((s) => s.name).join(', ')}.`);
  }
  if (report.checks.some((c) => c.status === 'unmeasured')) {
    lines.push('', `> **${t('gate.unmeasured.title', locale)}.**`);
  }
  lines.push('', '---', '', FOOTER[locale]);
  return lines.join('\n');
}

export function riskMarkdown(cls: Classification, locale: Locale, sample: boolean): string {
  const reasoning = locale === 'tr' && cls.reasoning_tr?.length ? cls.reasoning_tr : cls.reasoning;
  const limits = locale === 'tr' && cls.limits_tr?.length ? cls.limits_tr : cls.limits;
  const grey = locale === 'tr' && cls.grey_zone_reason_tr
    ? cls.grey_zone_reason_tr : cls.grey_zone_reason;
  const dutyHead = locale === 'tr'
    ? '| Madde | Yükümlülük | Kanıtı üreten |' : '| Article | Duty | Evidence produced by |';
  const lines = [
    ...head(`${t('nav.risk', locale)} — ${cls.system}`, locale, sample,
      [`${t('risk.confidence', locale)} ${cls.confidence.toFixed(2)}`,
        cls.regulation_version, `${t('risk.basis', locale)}: ${cls.evidence_basis}`]),
    '| | |', '|---|---|',
    `| ${locale === 'tr' ? 'Risk seviyesi' : 'Risk tier'} | **${cls.tier}** |`,
    `| ${t('risk.articles', locale)} | ${cls.articles.join(', ') || '—'} |`,
    `| ${t('risk.annex', locale)} | ${cls.annex_categories.join(', ') || '—'} |`,
  ];
  if (cls.grey_zone) lines.push('', `> **${t('risk.grey.title', locale)}** — ${grey}`);
  lines.push('', `## ${t('risk.reasoning', locale)}`, '', ...reasoning.map((r) => `- ${r}`));
  lines.push('', `## ${t('risk.obligations', locale)}`, '', dutyHead, '|---|---|---|',
    ...cls.obligations.map((o) => `| ${o.article} | `
      + `${locale === 'tr' && o.duty_tr ? o.duty_tr : o.duty} | \`${o.evidence_source}\` |`));
  if (cls.gpai_obligations.length) {
    lines.push('', `### ${t('risk.gpai', locale)}`, '', dutyHead, '|---|---|---|',
      ...cls.gpai_obligations.map((o) => `| ${o.article} | `
        + `${locale === 'tr' && o.duty_tr ? o.duty_tr : o.duty} | \`${o.evidence_source}\` |`));
  }
  if (limits.length) {
    lines.push('', `## ${t('common.limits', locale)}`, '', ...limits.map((l) => `- ${l}`));
  }
  lines.push('', '---', '', FOOTER[locale]);
  return lines.join('\n');
}

export function ragMarkdown(rag: RagReport, locale: Locale, sample: boolean): string {
  const lines = [
    ...head(`${t('nav.rag', locale)} — ${rag.subject}`, locale, sample,
      [`${rag.quality.total_chunks} ${t('rag.chunks_scanned', locale)}`,
        `session ${rag.session_id}`]),
    ...scoresTable(rag, locale),
    '', `## ${t('rag.bias_by_dimension', locale)}`, '',
    locale === 'tr' ? '| Boyut | Durum | Anma | Temsil | Çerçeveleme | Skor |'
      : '| Dimension | Assessed | Mentions | Representation | Framing | Score |',
    '|---|---|---:|---:|---:|---:|',
    ...rag.bias.dimensions.map((d) => `| ${d.dimension} | `
      + `${d.assessed ? '✓' : t('rag.unassessable', locale)} | ${d.total_mentions} | `
      + `${d.representation_score ?? '—'} | ${d.sentiment_score ?? '—'} | ${d.score ?? '—'} |`),
    ...findingsTable(rag, locale),
  ];
  if (rag.remediation?.length) {
    lines.push('', `## ${t('common.remediation', locale)}`, '', t('rag.remediation.note', locale), '');
    rag.remediation.forEach((r, i) => {
      lines.push(`### ${i + 1}. ${r.title}`, '',
        `\`${r.key}\` · impact **${r.impact}** · effort **${r.effort}**`
        + (r.article ? ` · ${r.article}` : ''), '', r.rationale, '',
        ...r.steps.map((s, j) => `${j + 1}. ${s}`), '', `> **Risk.** ${r.risk}`, '');
    });
  }
  lines.push(...limitsList(rag, locale), '', '---', '', FOOTER[locale]);
  return lines.join('\n');
}

export function vendorMarkdown(vendors: VendorReport[], locale: Locale, sample: boolean): string {
  const lines = head(t('nav.vendor', locale), locale, sample,
    [`${vendors.length} ${locale === 'tr' ? 'satıcı' : 'providers'}`]);
  vendors.forEach((v) => {
    lines.push('', `## ${v.provider}`, '', '| | |', '|---|---|',
      `| ${t('vendor.score', locale)} | ${v.scores.find((s) => s.name === 'vendor_score')?.value ?? '—'} |`,
      `| ${t('vendor.residency', locale)} | ${v.residency.verdict} (${v.residency.mechanism}) |`,
      `| ${t('vendor.optout', locale)} | ${v.training_optout.verdict} |`,
      `| ${locale === 'tr' ? 'Bilgi tarihi' : 'Facts as of'} | ${v.as_of}${v.stale ? ' ⚠️' : ''} |`,
      `| ${locale === 'tr' ? 'Tespit edilemeyen ölçüt' : 'Unknown criteria'} | ${v.unknown_criteria.length} / 24 |`,
      ...findingsTable(v, locale), ...limitsList(v, locale));
  });
  lines.push('', '---', '', FOOTER[locale]);
  return lines.join('\n');
}

export function guardMarkdown(g: GuardSummary, locale: Locale, sample: boolean): string {
  return [
    ...head(t('guard.title', locale), locale, sample, [`session ${g.session_id}`, `${g.duration_s}s`]),
    `> ${t('guard.no_values.body', locale)}`, '',
    '| | |', '|---|---|',
    `| ${t('guard.invocations', locale)} | ${g.calls} |`,
    `| ${t('guard.tokens', locale)} | ${g.tokens} |`,
    `| ${t('guard.blocked', locale)} | ${g.blocked_calls} |`,
    `| ${t('guard.degraded', locale)} | ${g.degraded_calls} |`,
    `| ${t('guard.masked_classes', locale)} | ${Object.entries(g.masked_entities).map(([k, n]) => `${k}: ${n}`).join(', ') || '—'} |`,
    `| ${t('guard.signatures', locale)} | ${g.signatures_triggered.join(', ') || '—'} |`,
    '', '---', '', FOOTER[locale],
  ].join('\n');
}
