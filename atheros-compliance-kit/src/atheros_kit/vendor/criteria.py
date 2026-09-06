"""The due-diligence matrix: 24 weighted criteria in 6 groups.

Weights encode what actually protects a customer, not what is easiest to verify.
A signed DPA and enforceable SCCs outweigh a status page by an order of
magnitude, and the scoring reflects that.

**`unknown` is penalised, not skipped.** This is the design decision that makes
the whole module worth running. Scoring only what a vendor volunteered rewards
opacity: the provider who answers nothing scores the same as the one who answers
everything favourably. Here, an unanswered question costs — 20% credit — because
"we could not establish this" is a real and adverse finding about a supplier.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Status = Literal["met", "partial", "not_met", "unknown"]

#: Credit awarded per status. `unknown` at 0.2 is the load-bearing number: high
#: enough that an unknown is not treated as a proven failure, low enough that a
#: vendor cannot score well by declining to answer.
STATUS_WEIGHT: dict[str, float] = {"met": 1.0, "partial": 0.5, "not_met": 0.0, "unknown": 0.2}


@dataclass(frozen=True)
class Criterion:
    key: str
    group: str
    question: str
    weight: int
    why: str
    article: str | None = None
    #: A criterion that cannot be `unknown` without blocking the assessment —
    #: these are the ones where not knowing is itself disqualifying.
    critical: bool = False

    def ask(self, locale: str = "en") -> str:
        """The question in the requested language.

        Turkish lives in QUESTIONS_TR below, keyed by the same `key`. A missing
        translation falls back to English rather than to an empty string: a
        vendor questionnaire with a blank question is worse than one in the
        wrong language.
        """
        return QUESTIONS_TR.get(self.key, self.question) if locale == "tr" else self.question


CRITERIA: list[Criterion] = [
    # ── 1. Certifications ────────────────────────────────────────────────────
    Criterion("iso_42001", "certifications", "ISO/IEC 42001 AI management system certification?", 8,
              "The only AI-specific management-system standard. Its absence is normal today and "
              "is becoming the differentiator in enterprise procurement.",
              "ISO 42001 §8.5"),
    Criterion("iso_27001", "certifications", "ISO/IEC 27001 information-security certification?", 7,
              "Baseline security governance. Its absence in an AI supplier is disqualifying for "
              "most regulated buyers."),
    Criterion("soc2_type2", "certifications", "SOC 2 Type II report available under NDA?", 6,
              "Type II tests controls over a period; Type I only describes them at a point. Accept "
              "Type I as `partial`, never as `met`."),
    # ── 2. Data protection ───────────────────────────────────────────────────
    Criterion("gdpr_dpa", "data_protection", "Signed GDPR Art. 28 data-processing agreement?", 10,
              "Without a DPA the customer is transferring personal data to a processor with no "
              "instrument governing it. This is the single highest-weighted criterion.",
              "GDPR Art. 28", critical=True),
    Criterion("sccs", "data_protection", "Standard Contractual Clauses in place for third-country transfers?", 9,
              "The transfer mechanism, where adequacy does not apply. Absence makes the transfer "
              "itself unlawful, not merely undocumented.",
              "GDPR Ch. V", critical=True),
    Criterion("subprocessor_list", "data_protection", "Published sub-processor list with change notice?", 6,
              "A processor's sub-processors are the customer's supply chain. Without notice, the "
              "customer cannot object before a change takes effect.",
              "GDPR Art. 28(2)"),
    Criterion("data_residency_choice", "data_protection", "Can the customer pin processing to a region?", 7,
              "Residency is what turns a policy commitment into a technical one."),
    # ── 3. Retention and training ────────────────────────────────────────────
    Criterion("zero_data_retention", "retention", "Zero data retention available AND enabled for this account?", 9,
              "Available and enabled are different facts. Score `partial` when it is offered but "
              "not switched on — that is the state most accounts are actually in.",
              critical=True),
    Criterion("training_optout", "retention", "Contractual guarantee that inputs are not used for model training?", 10,
              "The commitment that decides whether a prompt is a disclosure. Contractual, not a "
              "blog post.", critical=True),
    Criterion("log_retention_defined", "retention", "Is a log-retention period defined and bounded?", 5,
              "'We keep logs' without a period is indefinite retention."),
    Criterion("human_review_optout", "retention", "Can human review of prompts be disabled?", 7,
              "Human review means employees of the vendor read customer prompts. Frequently "
              "enabled by default for abuse monitoring."),
    # ── 4. Security ──────────────────────────────────────────────────────────
    Criterion("encryption_in_transit", "security", "TLS 1.2+ enforced on every endpoint?", 5,
              "Table stakes; scored so its absence is visible."),
    Criterion("encryption_at_rest", "security", "Data encrypted at rest with managed keys?", 5,
              "Table stakes."),
    Criterion("tenant_isolation", "security", "Logical or physical isolation between customers?", 7,
              "Determines whether one customer's prompt can surface in another's context."),
    Criterion("pen_test_report", "security", "Recent third-party penetration test, summary shareable?", 5,
              "An untested claim of security is a claim, not evidence."),
    Criterion("vuln_disclosure", "security", "Published vulnerability-disclosure policy?", 4,
              "A vendor with no disclosure route learns about its vulnerabilities last."),
    # ── 5. AI-specific ───────────────────────────────────────────────────────
    Criterion("model_card", "ai_specific", "Model cards published with intended use and limitations?", 6,
              "Feeds the customer's own Art. 13 duty. A provider who cannot describe the model's "
              "limits leaves its deployers unable to describe theirs.",
              "Art. 13"),
    Criterion("eval_reports", "ai_specific", "Safety and capability evaluations published?", 5,
              "Underpins the deployer's Art. 15 accuracy and robustness claims.", "Art. 15"),
    Criterion("incident_history_disclosed", "ai_specific", "Are AI incidents disclosed to customers?", 6,
              "A deployer's Art. 73 reporting duty depends on being told by the provider.",
              "Art. 73"),
    Criterion("deprecation_policy", "ai_specific", "Model deprecation notice period defined?", 5,
              "A model withdrawn at short notice invalidates every eval and every prompt tuned "
              "against it."),
    # ── 6. Operations ────────────────────────────────────────────────────────
    Criterion("sla", "operations", "Contractual availability SLA with remedies?", 5,
              "An SLA without remedies is a target."),
    Criterion("status_page", "operations", "Public status page with incident history?", 3,
              "Cheap to provide; its absence says something about operational maturity."),
    Criterion("support_tier", "operations", "Defined support tier and response times?", 3,
              "Determines how a production incident actually gets handled."),
    Criterion("exit_plan", "operations", "Documented data export and deletion on termination?", 6,
              "Lock-in is a governance risk, and deletion on termination is a GDPR Art. 28(3)(g) duty.",
              "GDPR Art. 28(3)(g)"),
]


#: Turkish questions, keyed by criterion. Kept beside CRITERIA rather than in the
#: message catalogue because the question IS the criterion: if the two languages
#: could be edited independently they would start asking different things, and
#: two vendors scored in two languages would stop being comparable.
QUESTIONS_TR: dict[str, str] = {
    "iso_42001": "ISO/IEC 42001 yapay zekâ yönetim sistemi sertifikası var mı?",
    "iso_27001": "ISO/IEC 27001 bilgi güvenliği sertifikası var mı?",
    "soc2_type2": "Gizlilik sözleşmesi altında SOC 2 Type II raporu sunuluyor mu?",
    "gdpr_dpa": "İmzalı GDPR Madde 28 veri işleme sözleşmesi var mı?",
    "sccs": "Üçüncü ülke aktarımları için Standart Sözleşme Maddeleri (SCC) mevcut mu?",
    "subprocessor_list": "Değişiklik bildirimiyle birlikte yayımlanmış alt işleyici listesi var mı?",
    "data_residency_choice": "Müşteri işlemeyi belirli bir bölgeye sabitleyebiliyor mu?",
    "zero_data_retention": "Sıfır veri saklama mevcut VE bu hesap için etkin mi?",
    "training_optout": "Girdilerin model eğitiminde kullanılmayacağına dair sözleşmesel garanti var mı?",
    "log_retention_defined": "Günlük saklama süresi tanımlı ve sınırlı mı?",
    "human_review_optout": "İstemlerin insan tarafından incelenmesi kapatılabiliyor mu?",
    "encryption_in_transit": "Her uç noktada TLS 1.2+ zorunlu tutuluyor mu?",
    "encryption_at_rest": "Veriler, yönetilen anahtarlarla beklemede şifreleniyor mu?",
    "tenant_isolation": "Müşteriler arasında mantıksal ya da fiziksel yalıtım var mı?",
    "pen_test_report": "Yakın tarihli üçüncü taraf sızma testi var mı, özeti paylaşılabiliyor mu?",
    "vuln_disclosure": "Yayımlanmış bir zafiyet bildirim politikası var mı?",
    "model_card": "Amaçlanan kullanım ve sınırlamaları içeren model kartları yayımlanıyor mu?",
    "eval_reports": "Güvenlik ve yetenek değerlendirmeleri yayımlanıyor mu?",
    "incident_history_disclosed": "Yapay zekâ olayları müşterilere bildiriliyor mu?",
    "deprecation_policy": "Model kullanımdan kaldırma bildirim süresi tanımlı mı?",
    "sla": "Yaptırımı olan sözleşmesel erişilebilirlik SLA'sı var mı?",
    "status_page": "Olay geçmişi içeren kamuya açık durum sayfası var mı?",
    "support_tier": "Tanımlı destek seviyesi ve yanıt süreleri var mı?",
    "exit_plan": "Fesih hâlinde veri dışa aktarımı ve silme belgelenmiş mi?",
}

CRITERIA_BY_KEY = {c.key: c for c in CRITERIA}

GROUPS = {
    "certifications": "Certifications and attestations",
    "data_protection": "Data protection and transfers",
    "retention": "Retention and model training",
    "security": "Security controls",
    "ai_specific": "AI-specific transparency",
    "operations": "Operational maturity",
}


def total_weight(criteria: list[Criterion] | None = None) -> int:
    return sum(c.weight for c in (criteria or CRITERIA))


def group_weights() -> dict[str, int]:
    out: dict[str, int] = {}
    for c in CRITERIA:
        out[c.group] = out.get(c.group, 0) + c.weight
    return out
