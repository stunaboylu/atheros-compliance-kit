/**
 * Where the Console gets its data.
 *
 * The Console is a READER. It never calls the customer's models, never touches
 * their corpus, and has no write path into anything the Kit assesses. That is a
 * deliberate trust property, not an unfinished feature: a governance viewer that
 * can reach into a production process is a new attack surface justified by
 * convenience.
 *
 * Two sources, in order:
 *   1. `EXPO_PUBLIC_REPORT_URL` — a static gate report your CI published.
 *   2. the bundled fixture — so the app runs, and demonstrates itself, offline.
 */
import bundled from '../data/atheros-report.json';
import ledgerFixture from '../data/audit_trail.json';
import type { GateReport, LedgerEntry } from './types';

const SUPPORTED_SCHEMA = 'atheros.gate/v1';

export interface LoadResult {
  report: GateReport;
  source: 'remote' | 'bundled';
  loadedAt: string;
  warning?: string;
}

/**
 * The bundled fixture, available synchronously.
 *
 * This is what static export renders. An async-only loader pre-renders the
 * loading spinner into every page, so the exported HTML carries no content —
 * which defeats the point of a static artefact you can host, archive, or print.
 * The fixture is a compile-time import, so there is no reason to await it.
 */
export function bundledReport(): LoadResult {
  return {
    report: bundled as unknown as GateReport,
    source: 'bundled',
    loadedAt: new Date(0).toISOString(),
  };
}

/** Whether a remote report is configured. When it is not, the sync path is final. */
export const hasRemoteSource = Boolean(process.env.EXPO_PUBLIC_REPORT_URL);

export async function loadReport(): Promise<LoadResult> {
  const url = process.env.EXPO_PUBLIC_REPORT_URL;
  const now = new Date().toISOString();

  if (url) {
    try {
      const res = await fetch(url, { headers: { Accept: 'application/json' } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as GateReport;
      if (json.schema !== SUPPORTED_SCHEMA) {
        // Render nothing rather than render it wrongly. Stale fields under
        // current labels is exactly the lie this Console exists to avoid.
        return {
          report: bundled as unknown as GateReport,
          source: 'bundled',
          loadedAt: now,
          warning:
            `The report at ${url} declares schema "${json.schema}", and this Console reads ` +
            `"${SUPPORTED_SCHEMA}". Showing the bundled sample instead of guessing at the mapping.`,
        };
      }
      return { report: json, source: 'remote', loadedAt: now };
    } catch (err) {
      return {
        report: bundled as unknown as GateReport,
        source: 'bundled',
        loadedAt: now,
        warning: `Could not load ${url} (${String(err)}). Showing the bundled sample.`,
      };
    }
  }
  return { report: bundled as unknown as GateReport, source: 'bundled', loadedAt: now };
}

export function loadLedger(): LedgerEntry[] {
  return ledgerFixture as unknown as LedgerEntry[];
}

/**
 * Re-verify the hash chain in the browser.
 *
 * Independent of the Python implementation on purpose: a verifier that shares
 * code with the writer can only prove they agree with each other. This one is a
 * second opinion, and it hashes the same field set — the event without the chain
 * fields — because a verifier that hashes a different set reports every intact
 * file as tampered and cannot distinguish one from a forgery.
 */
export async function verifyChain(
  entries: LedgerEntry[],
): Promise<{ intact: boolean; violations: string[] }> {
  const violations: string[] = [];
  let prev = 'GENESIS';

  const canonical = (v: unknown): string => {
    // JSON with sorted keys — must match json.dumps(..., sort_keys=True).
    if (v === null || typeof v !== 'object') return JSON.stringify(v);
    if (Array.isArray(v)) return `[${v.map(canonical).join(', ')}]`;
    const obj = v as Record<string, unknown>;
    const parts = Object.keys(obj)
      .sort()
      .map((k) => `${JSON.stringify(k)}: ${canonical(obj[k])}`);
    return `{${parts.join(', ')}}`;
  };

  for (let i = 0; i < entries.length; i++) {
    const e = entries[i];
    const { hash, previous_hash, ...payload } = e;
    if (previous_hash !== prev) {
      violations.push(
        `Line ${i + 1}: previous_hash mismatch (expected ${prev.slice(0, 12)}…, got ${(previous_hash || '∅').slice(0, 12)}…)`,
      );
    }
    const digest = await sha256(canonical(payload) + previous_hash);
    if (digest !== hash) {
      violations.push(
        `Line ${i + 1}: content altered (hash ${(hash || '∅').slice(0, 12)}… ≠ recomputed ${digest.slice(0, 12)}…)`,
      );
    }
    prev = hash;
  }
  return { intact: violations.length === 0, violations };
}

async function sha256(text: string): Promise<string> {
  const subtle = globalThis.crypto?.subtle;
  if (!subtle) return 'unavailable';
  const buf = await subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}
