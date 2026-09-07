"""The ISO/IEC 42001 clauses this product produces records for — and the ones it does not.

Both halves are the catalogue. A file that listed only what is covered would let
the absence of a clause read as an oversight rather than as a decision, and the
export built from it would be exactly the document this product exists to
prevent: one that looks broader than its evidence.

The distinction between `records` and `input` is load-bearing. Four clauses are
satisfied *by* the entries the Kit writes. Clause 6.1.2 is not: an EU AI Act risk
classification is an input to an organisation's AI risk assessment, not that
assessment. The ledger tags `euact` entries `6.1.2` so an auditor reading raw
JSONL knows where they belong; the export must not let that tag be read as the
clause being met.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Kind = Literal["records", "input"]


@dataclass(frozen=True)
class Clause:
    number: str
    title: str
    #: What the clause requires, in the auditor's terms — not what we produce.
    asks: str
    #: What the Kit contributes. Phrased as a contribution, never as compliance.
    produced_by: str
    #: Ledger `module` values whose entries evidence this clause. Must agree with
    #: AuditTrail.CLAUSES; a test asserts it, because the two drifting apart would
    #: silently drop a module's entries out of the export.
    modules: tuple[str, ...]
    kind: Kind = "records"


CLAUSES: tuple[Clause, ...] = (
    Clause(
        "6.1.2", "AI risk assessment",
        "The organisation establishes AI risk criteria and performs assessments that produce "
        "consistent, valid and comparable results.",
        "An EU AI Act risk classification per system, with the Annex III category and the "
        "evidence basis recorded. This is an input to the assessment; the risk criteria, the "
        "analysis and the evaluation remain the organisation's work.",
        ("euact",), kind="input",
    ),
    Clause(
        "8.3", "Operational controls",
        "Controls over the AI system in operation are implemented and their operation is "
        "documented.",
        "Per-call records from the guardrail wrapper: entity classes masked, injection "
        "signatures matched, whether the call was blocked, and which path answered it.",
        ("guard",),
    ),
    Clause(
        "8.4", "Data for AI systems",
        "The data used by the AI system is examined for quality, provenance and bias.",
        "Corpus quality, semantic drift and bias examinations with the resulting scores, or an "
        "explicit `unmeasured` where a score could not be established.",
        ("rag",),
    ),
    Clause(
        "8.5", "Third-party and customer relationships",
        "Suppliers of AI systems and services are assessed, and the division of "
        "responsibilities is established.",
        "Third-party due-diligence assessments across the weighted criteria matrix, with data "
        "residency and training opt-out recorded per provider.",
        ("vendor",),
    ),
    Clause(
        "9.1", "Monitoring, measurement, analysis and evaluation",
        "The organisation retains documented information as evidence of the monitoring and "
        "measurement results.",
        "The hash-chained ledger itself, plus every CI gate decision: which thresholds were "
        "evaluated, which checks did not run, and the exit code that followed.",
        ("cicd", "core"),
    ),
)

#: Turkish beside the English rather than in the message catalogue, for the same
#: reason the vendor questions live beside their criteria: the text IS the clause.
#: Two independently editable copies would start describing different standards.
TR: dict[str, tuple[str, str, str]] = {
    "6.1.2": (
        "Yapay zekâ risk değerlendirmesi",
        "Kuruluş yapay zekâ risk ölçütlerini belirler ve tutarlı, geçerli, karşılaştırılabilir "
        "sonuçlar üreten değerlendirmeler yapar.",
        "Sistem başına EU AI Act risk sınıflandırması; Ek III kategorisi ve kanıt dayanağı "
        "kayıtlıdır. Bu, değerlendirmeye bir girdidir; risk ölçütleri, analiz ve "
        "değerlendirmenin kendisi kuruluşun işi olarak kalır.",
    ),
    "8.3": (
        "Operasyonel kontroller",
        "Çalışan yapay zekâ sistemi üzerindeki kontroller uygulanır ve işleyişi belgelenir.",
        "Koruma sarmalayıcısından çağrı başına kayıtlar: maskelenen varlık sınıfları, eşleşen "
        "enjeksiyon imzaları, çağrının engellenip engellenmediği ve yanıtı hangi yolun verdiği.",
    ),
    "8.4": (
        "Yapay zekâ sistemleri için veri",
        "Sistemin kullandığı veri kalite, köken ve önyargı bakımından incelenir.",
        "Külliyat kalitesi, anlamsal kayma ve önyargı incelemeleri ile ortaya çıkan skorlar; "
        "skor tespit edilemediyse açık bir `unmeasured` kaydı.",
    ),
    "8.5": (
        "Üçüncü taraf ve müşteri ilişkileri",
        "Yapay zekâ sistem ve hizmet tedarikçileri değerlendirilir, sorumluluk paylaşımı "
        "belirlenir.",
        "Ağırlıklı kriter matrisi üzerinden üçüncü taraf inceleme değerlendirmeleri; sağlayıcı "
        "başına veri ikametgâhı ve eğitimden çıkma kayıtlıdır.",
    ),
    "9.1": (
        "İzleme, ölçme, analiz ve değerlendirme",
        "Kuruluş, izleme ve ölçme sonuçlarının kanıtı olarak belgelenmiş bilgiyi muhafaza eder.",
        "Zincir özetli defterin kendisi ve her CI kapısı kararı: hangi eşikler değerlendirildi, "
        "hangi kontroller çalışmadı ve ardından hangi çıkış kodu geldi.",
    ),
}

#: Rendered in every export, in both languages, with no flag to suppress it.
#: An evidence pack that lists five clauses and stops invites the reader to
#: supply the rest of the standard from imagination.
NOT_COVERED: dict[str, tuple[str, ...]] = {
    "en": (
        "Clause 4 — context of the organisation and the scope of the AI management system",
        "Clause 5 — leadership, the AI policy, and assigned roles and responsibilities",
        "Clause 6.1.3, 6.1.4 and 6.2 — risk treatment, the AI system impact assessment, "
        "and the AI objectives",
        "Clause 7 — competence, awareness, communication and control of documented information",
        "Clause 9.2 — the internal audit programme",
        "Clause 9.3 — management review",
        "Clause 10 — nonconformity, corrective action and continual improvement",
        "The Statement of Applicability",
        "The Annex A controls, as controls: the Kit evidences the operation of a few of them, "
        "and selects, justifies and documents none",
    ),
    "tr": (
        "Madde 4 — kuruluşun bağlamı ve yapay zekâ yönetim sisteminin kapsamı",
        "Madde 5 — liderlik, yapay zekâ politikası, atanmış rol ve sorumluluklar",
        "Madde 6.1.3, 6.1.4 ve 6.2 — risk işleme, yapay zekâ sistemi etki değerlendirmesi ve "
        "yapay zekâ amaçları",
        "Madde 7 — yeterlilik, farkındalık, iletişim ve belgelenmiş bilginin kontrolü",
        "Madde 9.2 — iç denetim programı",
        "Madde 9.3 — yönetim gözden geçirmesi",
        "Madde 10 — uygunsuzluk, düzeltici faaliyet ve sürekli iyileştirme",
        "Uygulanabilirlik Bildirimi",
        "Ek A kontrolleri, kontrol olarak: araç bunların birkaçının işlediğine dair kanıt üretir; "
        "hiçbirini seçmez, gerekçelendirmez ve belgelemez",
    ),
}


def title(number: str, locale: str = "en") -> str:
    clause = by_number(number)
    return TR[number][0] if locale == "tr" and number in TR else clause.title


def asks(number: str, locale: str = "en") -> str:
    clause = by_number(number)
    return TR[number][1] if locale == "tr" and number in TR else clause.asks


def produced_by(number: str, locale: str = "en") -> str:
    clause = by_number(number)
    return TR[number][2] if locale == "tr" and number in TR else clause.produced_by


def by_number(number: str) -> Clause:
    for clause in CLAUSES:
        if clause.number == number:
            return clause
    raise KeyError(number)


#: module -> clause number, derived rather than written twice.
MODULE_CLAUSE: dict[str, str] = {m: c.number for c in CLAUSES for m in c.modules}
