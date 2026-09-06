/**
 * The wire contract with the Python toolkit.
 *
 * These mirror `atheros_kit.core.report.Report.to_dict()` and the per-module
 * `to_dict()` payloads. `schema` is carried on every document so the Console can
 * refuse a version it does not understand rather than rendering it wrongly —
 * a governance dashboard showing stale fields under current labels is the
 * failure this field exists to prevent.
 */

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type Action = 'pass' | 'flag' | 'block';
export type Method = 'deterministic' | 'llm' | 'hybrid';
export type Coverage = 'covered' | 'partial' | 'missing' | 'not_applicable';
export type Band = 'good' | 'watch' | 'poor' | 'critical' | 'unmeasured';
export type RiskTier = 'unacceptable' | 'high' | 'limited' | 'minimal' | 'unknown';

export interface Finding {
  check: string;
  severity: Severity;
  detail: string;
  module: string;
  action: Action;
  article: string | null;
  evidence: Record<string, unknown>;
  remediation: string | null;
  /** The Kit emits every language on every finding, so a static export can
   *  toggle offline and an archived pack stays readable by a reviewer whose
   *  language was not chosen when the report was generated. */
  detail_tr?: string;
  remediation_tr?: string | null;
}

export interface Score {
  name: string;
  /** null means UNMEASURED. Never coerce it to 0 — they render differently and
   *  mean opposite things. */
  value: number | null;
  method: Method;
  degraded: boolean;
  threshold: number | null;
  band: Band;
  passed: boolean | null;
  basis: Record<string, unknown>;
}

export interface Report {
  schema: 'atheros.report/v1';
  module: string;
  subject: string;
  generated_at: string;
  session_id: string;
  degraded: boolean;
  worst_severity: Severity | null;
  scores: Score[];
  findings: Finding[];
  coverage: Record<string, Coverage>;
  limits: string[];
  limits_tr?: string[];
  locale?: 'en' | 'tr';
  metadata: Record<string, unknown>;
}

export interface RagReport extends Report {
  quality: {
    total_chunks: number;
    empty: number;
    near_empty: number;
    duplicate_groups: number;
    duplicate_chunks: number;
    near_duplicate_pairs: number;
    orphans: number;
    dimension_histogram: Record<string, number>;
    length_stats: Record<string, number>;
    pii_chunks: number;
    pii_categories: string[];
    near_dup_sampled: boolean;
    score: Score | null;
  };
  bias: {
    fairness_score: Score | null;
    chunks_scanned: number;
    assessed_dimensions: string[];
    /** Read this. What could not be measured is as important as what was. */
    unassessable: string[];
    affected_groups: string[];
    dimensions: Array<{
      dimension: string;
      assessed: boolean;
      reason: string;
      total_mentions: number;
      group_counts: Record<string, number>;
      representation_ratio: number | null;
      representation_score: number | null;
      group_sentiment: Record<string, number>;
      sentiment_spread: number | null;
      sentiment_score: number | null;
      score: number | null;
      underrepresented: string[];
      negatively_framed: string[];
    }>;
    limits: string[];
  };
  drift: {
    verdict: 'stable' | 'drifting' | 'shifted' | 'unmeasurable';
    centroid_similarity: number | null;
    centroid_informative: boolean;
    psi_mean: number | null;
    psi_max: number | null;
    psi_noise_floor: number | null;
    psi_stable_threshold: number | null;
    psi_dimensions_unstable: number;
    baseline_count: number;
    current_count: number;
    volume_ratio: number | null;
    limits: string[];
    score: Score | null;
  } | null;
  remediation: Recipe[];
}

export interface Recipe {
  key: string;
  title: string;
  rationale: string;
  steps: string[];
  impact: 'high' | 'medium' | 'low';
  effort: 'high' | 'medium' | 'low';
  risk: string;
  article: string | null;
  code: string | null;
  leverage: number;
}

export interface Classification {
  system: string;
  tier: RiskTier;
  confidence: number;
  grey_zone: boolean;
  grey_zone_reason: string | null;
  articles: string[];
  annex_categories: string[];
  reasoning: string[];
  obligations: Array<{
    article: string; duty: string; duty_tr?: string; evidence_source: string; note?: string;
  }>;
  gpai_obligations: Array<{
    article: string; duty: string; duty_tr?: string; evidence_source: string;
  }>;
  regulation_version: string;
  evidence_basis: 'indicator_matched' | 'sector_only' | 'no_indicator_matched';
  limits: string[];
  reasoning_tr?: string[];
  grey_zone_reason_tr?: string | null;
  limits_tr?: string[];
  obligations_tr?: never;
}

export interface VendorReport extends Report {
  provider: string;
  as_of: string;
  stale: boolean;
  customer_verified: boolean;
  group_scores: Record<string, number>;
  statuses: Record<string, 'met' | 'partial' | 'not_met' | 'unknown'>;
  unknown_criteria: string[];
  unknown_ratio: number;
  residency: {
    provider: string;
    processing_regions: string[];
    required_regions: string[];
    verdict: 'compliant' | 'requires_scc' | 'non_compliant' | 'unknown';
    mechanism: string;
    outside_required: string[];
    notes: string[];
  };
  training_optout: {
    provider: string;
    available: boolean | null;
    enabled: boolean | null;
    contractual: boolean | null;
    zdr_available: boolean | null;
    zdr_enabled: boolean | null;
    verdict: 'enforced' | 'available_not_evidenced' | 'not_available' | 'unknown';
    notes: string[];
  };
}

export interface GuardSummary {
  session_id: string;
  calls: number;
  tokens: number;
  degraded_calls: number;
  blocked_calls: number;
  masked_entities: Record<string, number>;
  signatures_triggered: string[];
  duration_s: number;
}

export interface GateReport {
  schema: 'atheros.gate/v1';
  session_id: string;
  passed: boolean;
  exit_code: number;
  checks: Array<{
    name: string;
    status: 'pass' | 'fail' | 'unmeasured' | 'skipped' | 'error';
    actual: unknown;
    threshold: unknown;
    detail: string;
  }>;
  reports: {
    rag?: RagReport;
    euact?: Classification;
    vendor?: VendorReport[];
    guard?: GuardSummary;
  };
  artefacts: string[];
}

export interface LedgerEntry {
  timestamp: string;
  session_id: string;
  module: string;
  event_type: string;
  iso_42001_clause: string;
  payload: Record<string, unknown>;
  hash: string;
  previous_hash: string;
}
