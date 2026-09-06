"""Bilingual message catalogue — English and Turkish, first class.

DESIGN

A `Finding` already carries a stable `check` identifier and structured
`evidence`. Those, not a prose string, are the finding's real content — so the
catalogue is keyed on the check and renders the sentence from parameters in the
requested language. The English `detail` a module writes stays on the object as
the fallback, which means:

  * a check with no catalogue entry renders in English rather than failing, and
  * adding a language is adding a dictionary, not touching forty call sites.

WHAT IS AND IS NOT TRANSLATED

Translated: finding sentences, remediation, report chrome, score bands, CLI
labels, and the limits — the limits especially, because a reader who cannot read
what the tool could not establish has been given false assurance in their own
language.

**Never translated:** article citations (`Art. 10`, `Annex III`), check
identifiers, module paths, enum values, hashes, and the regulation version.
These are identifiers. A Turkish report that says `Art. 10` cannot be matched
against an English one, and an auditor comparing two runs needs them to be the
same token. One rule holds throughout: never mix languages inside one
view — pick a locale for the whole document.

LEGAL TERMINOLOGY

Turkish regulatory wording follows the EU AI Act's Turkish-language commentary
and KVKK usage where they overlap. Terms that carry legal weight and have no
settled Turkish equivalent keep the English in parentheses on first use. The
non-certification vocabulary is translated conservatively — "değerlendirme"
(assessment), never "belgelendirme" (certification), and the banned-phrase lint
covers both languages.
"""
from __future__ import annotations

import os
from typing import Any

Locale = str
SUPPORTED: tuple[str, ...] = ("en", "tr")
DEFAULT_LOCALE = "en"

#: Tokens that must survive translation unchanged. Enforced by a test.
NEVER_TRANSLATED = (
    "Art.", "Annex", "ISO", "GDPR", "EU-", "atheros_kit", "rag.", "guard.", "euact.", "vendor.",
)


def resolve_locale(locale: str | None = None) -> Locale:
    """Explicit argument → ATHEROS_LOCALE → config default → en."""
    candidate = (locale or os.environ.get("ATHEROS_LOCALE") or DEFAULT_LOCALE).lower()
    candidate = candidate.split("-")[0].split("_")[0]
    return candidate if candidate in SUPPORTED else DEFAULT_LOCALE


# ── Report and CLI chrome ─────────────────────────────────────────────────────
UI: dict[str, dict[str, str]] = {
    "report.title": {"en": "{module} — {subject}", "tr": "{module} — {subject}"},
    "report.generated": {
        "en": "Generated {ts} · session {session}",
        "tr": "Oluşturulma {ts} · oturum {session}",
    },
    "report.degraded": {
        "en": "**Degraded run.** At least one score was produced on the deterministic fallback "
              "path rather than the configured model. Scores tagged `deterministic` below are not "
              "comparable to a full run.",
        "tr": "**Düşürülmüş çalışma.** En az bir skor, yapılandırılmış model yerine deterministik "
              "yedek yolda üretildi. Aşağıda `deterministic` etiketli skorlar tam bir çalışmayla "
              "karşılaştırılabilir değildir.",
    },
    "report.scores": {"en": "Scores", "tr": "Skorlar"},
    "report.findings": {"en": "Findings", "tr": "Bulgular"},
    "report.coverage": {"en": "Coverage", "tr": "Kapsam"},
    "report.limits": {"en": "Limits of this assessment", "tr": "Bu değerlendirmenin sınırları"},
    "report.no_findings": {
        "en": "No findings were raised by the checks that ran.",
        "tr": "Çalışan kontroller herhangi bir bulgu üretmedi.",
    },
    "report.no_scores": {"en": "No scores computed.", "tr": "Hesaplanan skor yok."},
    "report.footer": {
        "en": "This report is an automated assessment produced by the AtherosAI Developer "
              "Compliance Kit. It evidences what was measured and names what was not. It is not a "
              "certification and not a legal opinion.",
        "tr": "Bu rapor, AtherosAI Developer Compliance Kit tarafından üretilen otomatik bir "
              "değerlendirmedir. Ölçülen şeyi kanıtlar ve ölçülmeyeni açıkça belirtir. Bir "
              "belgelendirme değildir ve hukuki görüş niteliği taşımaz.",
    },
    "col.score": {"en": "Score", "tr": "Skor"},
    "col.value": {"en": "Value", "tr": "Değer"},
    "col.band": {"en": "Band", "tr": "Bant"},
    "col.method": {"en": "Method", "tr": "Yöntem"},
    "col.threshold": {"en": "Threshold", "tr": "Eşik"},
    "col.result": {"en": "Result", "tr": "Sonuç"},
    "col.severity": {"en": "Severity", "tr": "Önem"},
    "col.check": {"en": "Check", "tr": "Kontrol"},
    "col.article": {"en": "Article", "tr": "Madde"},
    "col.detail": {"en": "Detail", "tr": "Ayrıntı"},
    "col.action": {"en": "Action", "tr": "Eylem"},
    "col.section": {"en": "Section", "tr": "Bölüm"},
    "col.status": {"en": "Status", "tr": "Durum"},
    "col.duty": {"en": "Duty", "tr": "Yükümlülük"},
    "col.evidence_by": {"en": "Evidence produced by", "tr": "Kanıtı üreten"},
    "verdict.pass": {"en": "pass", "tr": "geçti"},
    "verdict.fail": {"en": "**fail**", "tr": "**başarısız**"},
    "verdict.unmeasured": {"en": "unmeasured", "tr": "ölçülmedi"},
    "band.good": {"en": "good", "tr": "iyi"},
    "band.watch": {"en": "watch", "tr": "izlenmeli"},
    "band.poor": {"en": "poor", "tr": "zayıf"},
    "band.critical": {"en": "critical", "tr": "kritik"},
    "band.unmeasured": {"en": "unmeasured", "tr": "ölçülmedi"},
    "severity.critical": {"en": "critical", "tr": "kritik"},
    "severity.high": {"en": "high", "tr": "yüksek"},
    "severity.medium": {"en": "medium", "tr": "orta"},
    "severity.low": {"en": "low", "tr": "düşük"},
    "severity.info": {"en": "info", "tr": "bilgi"},
    "action.pass": {"en": "pass", "tr": "geçir"},
    "action.flag": {"en": "flag", "tr": "işaretle"},
    "action.block": {"en": "block", "tr": "engelle"},
    "coverage.covered": {"en": "covered", "tr": "karşılandı"},
    "coverage.partial": {"en": "partial", "tr": "kısmi"},
    "coverage.missing": {"en": "missing", "tr": "eksik"},
    "coverage.not_applicable": {"en": "not applicable", "tr": "uygulanamaz"},
    "score.unmeasured_note": {
        "en": "Unmeasured. This is not a passing score — the measurement did not run or could not "
              "be computed.",
        "tr": "Ölçülmedi. Bu geçer bir skor değildir — ölçüm çalışmadı ya da hesaplanamadı.",
    },
    # ── gate ─────────────────────────────────────────────────────────────────
    "gate.title": {
        "en": "AtherosAI compliance gate — {result}",
        "tr": "AtherosAI uyum kapısı — {result}",
    },
    "gate.passed": {"en": "PASSED", "tr": "GEÇTİ"},
    "gate.failed": {"en": "FAILED", "tr": "BAŞARISIZ"},
    "gate.skipped_note": {
        "en": "**{n} check(s) did not run.** This gate covers less than its check list suggests: "
              "{names}.",
        "tr": "**{n} kontrol çalışmadı.** Bu kapı, kontrol listesinin ima ettiğinden daha azını "
              "kapsıyor: {names}.",
    },
    "gate.unmeasured_note": {
        "en": "**Unmeasured checks fail by design.** A score of `None` means the measurement did "
              "not run or could not be computed — it is not a pass.",
        "tr": "**Ölçülmeyen kontroller tasarım gereği başarısız olur.** `None` skoru, ölçümün "
              "çalışmadığı ya da hesaplanamadığı anlamına gelir — geçer değildir.",
    },
    "gate.footer": {
        "en": "Produced by the AtherosAI Developer Compliance Kit.",
        "tr": "AtherosAI Developer Compliance Kit tarafından üretilmiştir.",
    },
    "status.pass": {"en": "pass", "tr": "geçti"},
    "status.fail": {"en": "fail", "tr": "başarısız"},
    "status.unmeasured": {"en": "unmeasured", "tr": "ölçülmedi"},
    "status.skipped": {"en": "skipped", "tr": "atlandı"},
    "status.error": {"en": "error", "tr": "hata"},
    "gate.artefacts": {"en": "artefacts:", "tr": "çıktılar:"},
    "chain.intact": {"en": "intact", "tr": "sağlam"},
    "chain.violated": {"en": "VIOLATED", "tr": "İHLAL EDİLDİ"},
    "chain.entries": {
        "en": "{n} entr{plural} in {path}",
        "tr": "{path} içinde {n} kayıt",
    },
    "chain.violations": {
        "en": "{n} violation(s) in {path}",
        "tr": "{path} içinde {n} ihlal",
    },
    "chain.mismatch": {
        "en": "Line {line}: previous_hash mismatch (expected {expected}…, got {got}…)",
        "tr": "Satır {line}: previous_hash uyuşmuyor (beklenen {expected}…, gelen {got}…)",
    },
    "chain.altered": {
        "en": "Line {line}: content altered (hash {stored}… ≠ recomputed {recomputed}…)",
        "tr": "Satır {line}: içerik değiştirilmiş (özet {stored}… ≠ yeniden hesaplanan "
              "{recomputed}…)",
    },
    "chain.unparseable": {
        "en": "Line {line}: unparseable entry ({detail})",
        "tr": "Satır {line}: ayrıştırılamayan kayıt ({detail})",
    },
    "chain.more": {"en": "… {n} more", "tr": "… {n} tane daha"},
    "gate.no_threshold": {"en": "no threshold configured", "tr": "eşik yapılandırılmamış"},
    "gate.unmeasured_detail": {
        "en": "the score could not be computed — unmeasured is not a pass",
        "tr": "skor hesaplanamadı — ölçülmemiş olmak geçer değildir",
    },
    "gate.not_configured": {"en": "module not configured", "tr": "modül yapılandırılmamış"},
    "gate.no_baseline": {
        "en": "no baseline supplied, so drift was not measured",
        "tr": "referans anlık görüntü verilmedi, bu nedenle kayma ölçülmedi",
    },
    # ── dossier ──────────────────────────────────────────────────────────────
    "dossier.title": {
        "en": "Technical Documentation — {system}",
        "tr": "Teknik Dokümantasyon — {system}",
    },
    "dossier.subtitle": {
        "en": "Annex IV, Regulation (EU) 2024/1689 · regulation version `{version}` · generated {ts}",
        "tr": "Annex IV, (AB) 2024/1689 sayılı Tüzük · mevzuat sürümü `{version}` · oluşturulma {ts}",
    },
    "dossier.classification": {"en": "Classification", "tr": "Sınıflandırma"},
    "dossier.risk_tier": {"en": "Risk tier", "tr": "Risk seviyesi"},
    "dossier.confidence": {"en": "Confidence", "tr": "Güven"},
    "dossier.grey_zone": {"en": "Grey zone", "tr": "Gri bölge"},
    "dossier.articles": {"en": "Articles", "tr": "Maddeler"},
    "dossier.annex_categories": {"en": "Annex III categories", "tr": "Annex III kategorileri"},
    "dossier.basis": {"en": "Basis", "tr": "Dayanak"},
    "dossier.reasoning": {"en": "Reasoning", "tr": "Gerekçe"},
    "dossier.completeness": {"en": "Completeness — {pct}%", "tr": "Tamlık — %{pct}"},
    "dossier.incomplete": {
        "en": "**This document is incomplete.** {gaps} of {total} sections are missing or partial. "
              "It is not ready for a conformity assessment and must not be presented as though it were.",
        "tr": "**Bu belge eksiktir.** {total} bölümden {gaps} tanesi eksik ya da kısmidir. Uygunluk "
              "değerlendirmesine hazır değildir ve öyleymiş gibi sunulmamalıdır.",
    },
    "dossier.gap": {"en": "**Gap.**", "tr": "**Boşluk.**"},
    "dossier.required": {"en": "_Required:_", "tr": "_Gerekli:_"},
    "dossier.evidence": {"en": "Evidence:", "tr": "Kanıt:"},
    "dossier.obligations": {"en": "Applicable obligations", "tr": "Uygulanabilir yükümlülükler"},
    "dossier.gpai": {
        "en": "General-purpose AI model duties (Chapter V)",
        "tr": "Genel amaçlı yapay zekâ modeli yükümlülükleri (Bölüm V)",
    },
    "dossier.footer": {
        "en": "Generated by the AtherosAI Developer Compliance Kit. This is a structured draft "
              "assembled from automated evidence. It is not a conformity assessment, not a "
              "certification, and not legal advice. Sections marked missing or partial require "
              "human authorship before this document can serve its Art. 11 purpose.",
        "tr": "AtherosAI Developer Compliance Kit tarafından oluşturulmuştur. Bu, otomatik "
              "kanıtlardan derlenmiş yapılandırılmış bir taslaktır. Uygunluk değerlendirmesi, "
              "belgelendirme veya hukuki tavsiye değildir. Eksik ya da kısmi işaretli bölümler, bu "
              "belgenin Art. 11 amacına hizmet edebilmesi için insan tarafından yazılmalıdır.",
    },
    # ── remediation ──────────────────────────────────────────────────────────
    "remediation.title": {"en": "Remediation plan", "tr": "İyileştirme planı"},
    "remediation.intro": {
        "en": "Ordered by leverage (expected impact against effort). **Nothing here runs "
              "automatically** — the Kit's connection to your corpus is read-only by design.",
        "tr": "Kaldıraç sırasına göre (beklenen etki / efor). **Buradaki hiçbir şey otomatik "
              "çalışmaz** — Kit'in külliyatınıza bağlantısı tasarım gereği salt okunurdur.",
    },
    "remediation.steps": {"en": "**Steps**", "tr": "**Adımlar**"},
    "remediation.risk": {"en": "**Risk.**", "tr": "**Risk.**"},
    "remediation.impact": {"en": "impact", "tr": "etki"},
    "remediation.effort": {"en": "effort", "tr": "efor"},
    "remediation.none": {
        "en": "No remediation recipes: no finding in this report has a known recipe.",
        "tr": "İyileştirme tarifi yok: bu rapordaki hiçbir bulgunun bilinen bir tarifi yok.",
    },
}


def ui(key: str, locale: Locale = DEFAULT_LOCALE, **params: Any) -> str:
    """Chrome string. Missing key returns the key itself — visible, not silent."""
    entry = UI.get(key)
    if entry is None:
        return key
    text = entry.get(locale) or entry.get(DEFAULT_LOCALE, key)
    return text.format(**params) if params else text


def enum(prefix: str, value: str, locale: Locale = DEFAULT_LOCALE) -> str:
    """Localise an enum's DISPLAY form. The wire value is never translated."""
    return ui(f"{prefix}.{value}", locale) if f"{prefix}.{value}" in UI else value


# ── Finding sentences ─────────────────────────────────────────────────────────
# Keyed on the check identifier (the part before any ".suffix"). Each entry holds
# `detail` and, where one exists, `remediation`. The English text here must stay
# identical to what the module writes, so that switching language changes the
# language and nothing else — a report that also changes its claims when
# translated is two reports.
FINDINGS: dict[str, dict[str, dict[str, str]]] = {
    # ── guard ────────────────────────────────────────────────────────────────
    "secret_in_prompt": {
        "detail": {
            "en": "credential-shaped values present in the prompt: {categories}",
            "tr": "istemde kimlik bilgisi biçimli değerler var: {categories}",
        },
        "remediation": {
            "en": "Remove the credential at the source and rotate it; masking is not rotation.",
            "tr": "Kimlik bilgisini kaynağından kaldırın ve döndürün; maskeleme döndürme değildir.",
        },
    },
    "pii_masked": {
        "detail": {
            "en": "personal-data categories masked before egress: {categories}",
            "tr": "dışarı çıkmadan önce maskelenen kişisel veri kategorileri: {categories}",
        },
    },
    "empty_response": {
        "detail": {
            "en": "the provider returned no content",
            "tr": "sağlayıcı hiçbir içerik döndürmedi",
        },
        "remediation": {
            "en": "Retry, or fall back — do not present an empty answer as a result.",
            "tr": "Yeniden deneyin ya da yedeğe düşün — boş bir yanıtı sonuç olarak sunmayın.",
        },
    },
    "provider_refusal": {
        "detail": {
            "en": "the provider declined the request rather than answering it",
            "tr": "sağlayıcı isteği yanıtlamak yerine reddetti",
        },
        "remediation": {
            "en": "Substitute the configured fallback; do not surface the refusal as an answer.",
            "tr": "Yapılandırılmış yedeği kullanın; reddi bir yanıtmış gibi göstermeyin.",
        },
    },
    "assurance_overclaim": {
        "detail": {
            "en": "model output asserts compliance or certainty that no evidence supports",
            "tr": "model çıktısı, hiçbir kanıtın desteklemediği bir uyum ya da kesinlik iddia ediyor",
        },
        "remediation": {
            "en": "Never let this text reach a user or a report. Compliance conclusions come from "
                  "evidence-graded assessment, not from model prose.",
            "tr": "Bu metnin bir kullanıcıya ya da rapora ulaşmasına asla izin vermeyin. Uyum "
                  "sonuçları, model metninden değil kanıt dereceli değerlendirmeden gelir.",
        },
    },
    "placeholder_hallucination": {
        "detail": {
            "en": "the response contains {count} placeholder(s) this session never issued",
            "tr": "yanıt, bu oturumun hiç üretmediği {count} yer tutucu içeriyor",
        },
        "remediation": {
            "en": "Do not resolve invented placeholders; treat the answer as unreliable.",
            "tr": "Uydurulmuş yer tutucuları çözmeyin; yanıtı güvenilmez sayın.",
        },
    },
    # ── rag: quality ─────────────────────────────────────────────────────────
    "empty_corpus": {
        "detail": {
            "en": "the connector returned no chunks",
            "tr": "bağlayıcı hiç parça döndürmedi",
        },
        "remediation": {
            "en": "Check the collection name and namespace before trusting any retrieval metric.",
            "tr": "Herhangi bir getirme metriğine güvenmeden önce koleksiyon adını ve ad alanını "
                  "kontrol edin.",
        },
    },
    "empty_chunks": {
        "detail": {
            "en": "{count} chunk(s) contain no text but occupy a retrieval slot",
            "tr": "{count} parça metin içermiyor ancak bir getirme yuvasını işgal ediyor",
        },
        "remediation": {
            "en": "Delete them, then re-check the extraction step that produced them.",
            "tr": "Bunları silin, ardından onları üreten çıkarma adımını yeniden kontrol edin.",
        },
    },
    "near_empty_chunks": {
        "detail": {
            "en": "{count} chunk(s) under {threshold} characters carry no standalone meaning",
            "tr": "{threshold} karakterin altındaki {count} parça tek başına anlam taşımıyor",
        },
        "remediation": {
            "en": "Merge with an adjacent chunk or drop; revisit the chunking boundary.",
            "tr": "Komşu bir parçayla birleştirin ya da atın; parçalama sınırını gözden geçirin.",
        },
    },
    "unembedded_chunks": {
        "detail": {
            "en": "{count} chunk(s) have no embedding and cannot be retrieved at all",
            "tr": "{count} parçanın gömmesi yok ve hiçbir şekilde getirilemez",
        },
        "remediation": {
            "en": "Re-run embedding for these ids. They are in the corpus and absent from the "
                  "index — every recall figure computed over this collection is optimistic by "
                  "this amount.",
            "tr": "Bu kimlikler için gömmeyi yeniden çalıştırın. Külliyatta varlar ama dizinde "
                  "yoklar — bu koleksiyon üzerinde hesaplanan her geri çağırma değeri bu kadar "
                  "iyimserdir.",
        },
    },
    "mixed_embedding_dimensions": {
        "detail": {
            "en": "chunks carry {count} different vector dimensions ({histogram})",
            "tr": "parçalar {count} farklı vektör boyutu taşıyor ({histogram})",
        },
        "remediation": {
            "en": "Two embedding models have written into one collection. Distances across them "
                  "are meaningless, so retrieval quality cannot be assessed until the collection "
                  "is re-embedded with one model.",
            "tr": "Tek bir koleksiyona iki farklı gömme modeli yazmış. Aralarındaki uzaklıklar "
                  "anlamsızdır; koleksiyon tek bir modelle yeniden gömülene kadar getirme "
                  "kalitesi değerlendirilemez.",
        },
    },
    "duplicate_chunks": {
        "detail": {
            "en": "{redundant} redundant copies across {groups} group(s) ({pct}% of the corpus)",
            "tr": "{groups} grup içinde {redundant} gereksiz kopya (külliyatın %{pct}'i)",
        },
        "remediation": {
            "en": "De-duplicate by content hash before the next ingestion, and make the ingestion "
                  "idempotent so this does not recur.",
            "tr": "Bir sonraki alımdan önce içerik özetine göre tekilleştirin ve tekrarlanmaması "
                  "için alımı idempotent hale getirin.",
        },
    },
    "near_duplicate_chunks": {
        "detail": {
            "en": "{pairs} chunk pair(s) exceed {threshold} shingle overlap",
            "tr": "{pairs} parça çifti {threshold} örtüşme eşiğini aşıyor",
        },
        "remediation": {
            "en": "Usually shared boilerplate. Strip headers and footers at ingestion rather than "
                  "deleting the documents.",
            "tr": "Genellikle ortak şablon metindir. Belgeleri silmek yerine alım sırasında üst ve "
                  "alt bilgileri ayıklayın.",
        },
    },
    "oversized_chunks": {
        "detail": {
            "en": "{count} chunk(s) exceed 4× the median length",
            "tr": "{count} parça, ortanca uzunluğun 4 katını aşıyor",
        },
        "remediation": {
            "en": "Re-chunk these documents; an oversized chunk buries its answer.",
            "tr": "Bu belgeleri yeniden parçalayın; aşırı büyük bir parça yanıtını gömer.",
        },
    },
    "personal_data_in_corpus": {
        "detail": {
            "en": "{count} chunk(s) contain structurally recognisable personal data ({categories})",
            "tr": "{count} parça yapısal olarak tanınabilir kişisel veri içeriyor ({categories})",
        },
        "remediation": {
            "en": "Redact at ingestion. Note that these detectors are structural — names and "
                  "free-text identifiers are not caught, so this count is a floor, never a total.",
            "tr": "Alım sırasında maskeleyin. Bu dedektörler yapısaldır — isimler ve serbest metin "
                  "tanımlayıcıları yakalanmaz, dolayısıyla bu sayı bir alt sınırdır, toplam değil.",
        },
    },
    # ── rag: drift ───────────────────────────────────────────────────────────
    "drift_unmeasurable": {
        "detail": {
            "en": "no embeddings available in one or both snapshots",
            "tr": "anlık görüntülerin birinde veya ikisinde gömme yok",
        },
        "remediation": {
            "en": "Export vectors alongside text, or the corpus cannot be monitored.",
            "tr": "Vektörleri metinle birlikte dışa aktarın, aksi halde külliyat izlenemez.",
        },
    },
    "drift_dimension_mismatch": {
        "detail": {
            "en": "baseline and current embeddings have different dimensions: {dims}",
            "tr": "referans ve güncel gömmeler farklı boyutlarda: {dims}",
        },
        "remediation": {
            "en": "Re-embed one snapshot with the other's model before comparing. Until then every "
                  "retrieval metric spanning these two is meaningless.",
            "tr": "Karşılaştırmadan önce bir anlık görüntüyü diğerinin modeliyle yeniden gömün. O "
                  "zamana kadar bu ikisini kapsayan her getirme metriği anlamsızdır.",
        },
    },
    "corpus_semantic_shift": {
        "detail": {
            "en": "the corpus has materially shifted ({cos}mean PSI {psi}, {unstable} unstable "
                  "dimensions)",
            "tr": "külliyat esaslı biçimde kaymış ({cos}ortalama PSI {psi}, {unstable} kararsız "
                  "boyut)",
        },
        "remediation": {
            "en": "Re-run retrieval evaluation before trusting current answer quality. Recall "
                  "figures measured on the baseline no longer describe this corpus.",
            "tr": "Güncel yanıt kalitesine güvenmeden önce getirme değerlendirmesini yeniden "
                  "çalıştırın. Referans üzerinde ölçülen geri çağırma değerleri artık bu "
                  "külliyatı tarif etmiyor.",
        },
    },
    "corpus_drift": {
        "detail": {
            "en": "early drift signal ({cos}mean PSI {psi})",
            "tr": "erken kayma sinyali ({cos}ortalama PSI {psi})",
        },
        "remediation": {
            "en": "Watch it. Set this run as the new baseline only if the change was intended.",
            "tr": "İzleyin. Bu çalışmayı yeni referans yapmayı yalnızca değişiklik kasıtlıysa "
                  "düşünün.",
        },
    },
    "corpus_volume_change": {
        "detail": {
            "en": "the corpus changed size by {ratio}× ({before} → {after} chunks)",
            "tr": "külliyatın boyutu {ratio}× değişti ({before} → {after} parça)",
        },
        "remediation": {
            "en": "A corpus that halved or doubled has changed regardless of its geometry. Confirm "
                  "the ingestion did what was intended.",
            "tr": "Yarıya inen ya da ikiye katlanan bir külliyat, geometrisinden bağımsız olarak "
                  "değişmiştir. Alımın amaçlananı yaptığını doğrulayın.",
        },
    },
    # ── rag: bias ────────────────────────────────────────────────────────────
    "bias_unassessable": {
        "detail": {
            "en": "'{dimension}' could not be assessed: {reason}",
            "tr": "'{dimension}' değerlendirilemedi: {reason_tr}",
        },
        "remediation": {
            "en": "Either the corpus does not discuss this dimension, or it does so in vocabulary "
                  "the lexicon does not carry. Extend it via `extra_dimensions=` before concluding "
                  "the first.",
            "tr": "Ya külliyat bu boyuttan söz etmiyor ya da sözlükte bulunmayan bir kelime "
                  "dağarcığıyla söz ediyor. İlkine karar vermeden önce `extra_dimensions=` ile "
                  "genişletin.",
        },
    },
    "representation_imbalance": {
        "detail": {
            "en": "'{dimension}' fails the four-fifths rule (ratio {ratio}); under-represented: "
                  "{groups}",
            "tr": "'{dimension}' beşte-dört kuralını karşılamıyor (oran {ratio}); yetersiz temsil: "
                  "{groups}",
        },
        "remediation": {
            "en": "Augment the corpus for the under-represented groups, or down-sample the "
                  "dominant one. Do not re-weight retrieval to hide it.",
            "tr": "Yetersiz temsil edilen gruplar için külliyatı zenginleştirin ya da baskın olanı "
                  "seyreltin. Gizlemek için getirmeyi yeniden ağırlıklandırmayın.",
        },
    },
    "framing_skew": {
        "detail": {
            "en": "'{dimension}' shows a contextual-language gap of {spread} between groups; "
                  "negatively framed: {groups}",
            "tr": "'{dimension}' gruplar arasında {spread} bağlamsal dil farkı gösteriyor; olumsuz "
                  "çerçevelenen: {groups}",
        },
        "remediation": {
            "en": "The corpus is balanced in counts and unbalanced in language. Review the source "
                  "documents for the affected groups; this is the form of bias that survives a "
                  "representation audit.",
            "tr": "Külliyat sayıca dengeli, dil bakımından dengesiz. Etkilenen gruplar için kaynak "
                  "belgeleri gözden geçirin; bu, temsil denetiminden sağ çıkan önyargı biçimidir.",
        },
    },
    "fairness_score_below_threshold": {
        "detail": {
            "en": "Fairness Score {score}/100 across {n} assessed dimension(s)",
            "tr": "Adillik Skoru {score}/100, {n} değerlendirilen boyut üzerinden",
        },
        "remediation": {
            "en": "See the per-dimension findings; remediation recipes are in "
                  "`rag.remediation.recommend()`.",
            "tr": "Boyut bazlı bulgulara bakın; iyileştirme tarifleri "
                  "`rag.remediation.recommend()` içinde.",
        },
    },
    # ── euact ────────────────────────────────────────────────────────────────
    "eu_ai_act_tier": {
        "detail": {
            "en": "classified {tier} (confidence {confidence}) — {reason}",
            "tr": "{tier} olarak sınıflandırıldı (güven {confidence}) — {reason_tr}",
        },
    },
    "classification_grey_zone": {
        "detail": {"en": "{reason}", "tr": "{reason_tr}"},
        "remediation": {
            "en": "Route to a human reviewer. Do not act on the tier alone.",
            "tr": "Bir insan gözden geçirene yönlendirin. Yalnızca seviyeye dayanarak hareket "
                  "etmeyin.",
        },
    },
    "annex_iv_gap": {
        "detail": {
            "en": "{annex_ref} '{title}' is {coverage}: {note}",
            "tr": "{annex_ref} '{title}' durumu {coverage}: {note}",
        },
    },
    # ── vendor ───────────────────────────────────────────────────────────────
    "vendor_unknown": {
        "detail": {
            "en": "{question} — not established{critical}",
            "tr": "{question_tr} — tespit edilemedi{critical}",
        },
    },
    "vendor_gap": {
        "detail": {"en": "{question} — NOT met", "tr": "{question_tr} — KARŞILANMIYOR"},
    },
    "vendor_partial": {
        "detail": {
            "en": "{question} — only partially met, on a critical criterion",
            "tr": "{question_tr} — kritik bir ölçütte yalnızca kısmen karşılanıyor",
        },
    },
    "residency_unknown": {
        "detail": {
            "en": "processing regions for {provider} could not be established",
            "tr": "{provider} için işleme bölgeleri tespit edilemedi",
        },
        "remediation": {
            "en": "Request the processing locations and sub-processor list from the vendor.",
            "tr": "Satıcıdan işleme konumlarını ve alt işleyici listesini talep edin.",
        },
    },
    "transfer_no_mechanism": {
        "detail": {
            "en": "{provider} processes in {regions}, which has neither an adequacy decision nor a "
                  "declared transfer mechanism",
            "tr": "{provider} {regions} bölgesinde işliyor; burada ne yeterlilik kararı ne de "
                  "beyan edilmiş bir aktarım mekanizması var",
        },
        "remediation": {
            "en": "Do not transfer personal data on this route. Pin processing to an adequate "
                  "region, or execute SCCs with a transfer impact assessment.",
            "tr": "Bu rota üzerinden kişisel veri aktarmayın. İşlemeyi yeterli bir bölgeye "
                  "sabitleyin ya da aktarım etki değerlendirmesiyle birlikte SCC imzalayın.",
        },
    },
    "dpf_certification_unverified": {
        "detail": {
            "en": "{provider} processes in {regions}. Adequacy there depends on the recipient's "
                  "own Data Privacy Framework certification, which has not been confirmed for "
                  "this vendor",
            "tr": "{provider} {regions} bölgesinde işliyor. Oradaki yeterlilik, alıcının kendi "
                  "Data Privacy Framework sertifikasyonuna bağlıdır ve bu satıcı için "
                  "doğrulanmamıştır",
        },
        "remediation": {
            "en": "Check the vendor on the DPF participant list. If it is not certified, the "
                  "transfer needs SCCs and a transfer impact assessment.",
            "tr": "Satıcıyı DPF katılımcı listesinde kontrol edin. Sertifikalı değilse aktarım, "
                  "SCC ve aktarım etki değerlendirmesi gerektirir.",
        },
    },
    "transfer_requires_scc": {
        "detail": {
            "en": "{provider} processes outside {required} ({regions}); SCCs are declared and must "
                  "be evidenced",
            "tr": "{provider} {required} dışında işliyor ({regions}); SCC beyan edilmiş ve "
                  "kanıtlanması gerekiyor",
        },
        "remediation": {
            "en": "Attach the executed SCCs and the transfer impact assessment to the vendor file. "
                  "A declared mechanism is not an evidenced one.",
            "tr": "İmzalanmış SCC'leri ve aktarım etki değerlendirmesini satıcı dosyasına ekleyin. "
                  "Beyan edilmiş bir mekanizma, kanıtlanmış bir mekanizma değildir.",
        },
    },
    "transfer_mechanism_unknown": {
        "detail": {
            "en": "{provider} processes outside the required region(s) and no transfer mechanism "
                  "is recorded",
            "tr": "{provider} gerekli bölgelerin dışında işliyor ve kayıtlı bir aktarım "
                  "mekanizması yok",
        },
        "remediation": {
            "en": "Establish the mechanism in writing before the next transfer.",
            "tr": "Bir sonraki aktarımdan önce mekanizmayı yazılı olarak belirleyin.",
        },
    },
    "training_optout_unavailable": {
        "detail": {
            "en": "{provider} offers no opt-out from using inputs for model training",
            "tr": "{provider}, girdilerin model eğitiminde kullanılmasından çıkma seçeneği sunmuyor",
        },
        "remediation": {
            "en": "Do not send confidential or personal data to this provider. Every prompt is a "
                  "disclosure into a training corpus you cannot recall.",
            "tr": "Bu sağlayıcıya gizli ya da kişisel veri göndermeyin. Her istem, geri "
                  "çağıramayacağınız bir eğitim külliyatına yapılmış bir ifşadır.",
        },
    },
    "training_optout_unknown": {
        "detail": {
            "en": "whether {provider} uses inputs for training could not be established",
            "tr": "{provider}'in girdileri eğitim için kullanıp kullanmadığı tespit edilemedi",
        },
        "remediation": {
            "en": "Get this in writing before the next production call. An unanswered question "
                  "here is not a neutral fact.",
            "tr": "Bir sonraki üretim çağrısından önce bunu yazılı olarak alın. Buradaki yanıtsız "
                  "bir soru tarafsız bir olgu değildir.",
        },
    },
    "training_optout_not_evidenced": {
        "detail": {
            "en": "{provider} offers a training opt-out, but it is {missing}",
            "tr": "{provider} eğitimden çıkma seçeneği sunuyor, ancak {missing_tr}",
        },
        "remediation": {
            "en": "Confirm the setting in the account console, then get the commitment into the "
                  "DPA. An opt-out that exists and is off protects nothing.",
            "tr": "Ayarı hesap konsolunda doğrulayın, ardından taahhüdü veri işleme sözleşmesine "
                  "yazdırın. Var olan ama kapalı bir çıkma seçeneği hiçbir şeyi korumaz.",
        },
    },
    "zdr_not_enabled": {
        "detail": {
            "en": "{provider} supports zero data retention but it is not confirmed enabled for "
                  "this account",
            "tr": "{provider} sıfır veri saklamayı destekliyor ancak bu hesap için etkin olduğu "
                  "doğrulanmadı",
        },
        "remediation": {
            "en": "Enable ZDR, or record the business reason for retaining prompts and the "
                  "retention period that applies to them.",
            "tr": "ZDR'yi etkinleştirin ya da istemlerin saklanmasına ilişkin iş gerekçesini ve "
                  "geçerli saklama süresini kayda geçirin.",
        },
    },
    "vendor_facts_stale": {
        "detail": {
            "en": "the facts used for this assessment are dated {as_of}{age}",
            "tr": "bu değerlendirmede kullanılan bilgiler {as_of} tarihli{age_tr}",
        },
        "remediation": {
            "en": "Re-verify with the vendor and pass the answers via `overrides=`. Vendor terms "
                  "change without notice.",
            "tr": "Satıcıyla yeniden doğrulayın ve yanıtları `overrides=` ile geçirin. Satıcı "
                  "koşulları haber verilmeksizin değişir.",
        },
    },
}


# ── Classification reasoning fragments ────────────────────────────────────────
# The classifier builds its account of WHY in both languages as it goes, rather
# than translating a finished English sentence. A post-hoc translation of legal
# reasoning is where meaning is lost, and this is the sentence a person signs.
REASONING: dict[str, dict[str, str]] = {
    "prohibited": {
        "en": "matches a practice prohibited under Art. 5: {category} ({hits})",
        "tr": "Art. 5 kapsamında yasaklanmış bir uygulamayla eşleşiyor: {category} ({hits})",
    },
    "annex_i": {
        "en": "safety component of a product covered by Annex I Union harmonisation "
              "legislation: {matches}",
        "tr": "Annex I Birlik uyumlaştırma mevzuatı kapsamındaki bir ürünün güvenlik bileşeni: "
              "{matches}",
    },
    "annex_iii": {
        "en": "use case matches Annex III {category} ({hits})",
        "tr": "kullanım senaryosu Annex III {category} ile eşleşiyor ({hits})",
    },
    "sector": {
        "en": "deployed in a high-risk sector: {sector}",
        "tr": "yüksek riskli bir sektörde konuşlandırılmış: {sector}",
    },
    "oversight": {
        "en": "operates autonomously with no recorded human oversight — Art. 14 obligations "
              "need explicit review",
        "tr": "kayıtlı insan gözetimi olmadan özerk çalışıyor — Art. 14 yükümlülükleri açık "
              "bir gözden geçirme gerektiriyor",
    },
    "sector_only": {
        "en": "deployed in a high-risk sector ({sector}) but no Annex III use case was "
              "recognised in the description provided",
        "tr": "yüksek riskli bir sektörde ({sector}) konuşlandırılmış ancak verilen açıklamada "
              "Annex III kapsamında bir kullanım senaryosu tanınmadı",
    },
    "transparency": {
        "en": "transparency obligations attach: {matches}",
        "tr": "şeffaflık yükümlülükleri doğuyor: {matches}",
    },
    "minimal": {
        "en": "no prohibited practice, Annex I product, Annex III use case, or Art. 50 "
              "transparency trigger was recognised in the description provided",
        "tr": "verilen açıklamada yasaklanmış bir uygulama, Annex I ürünü, Annex III kullanım "
              "senaryosu ya da Art. 50 şeffaflık tetikleyicisi tanınmadı",
    },
}

# ── Grey-zone and limit sentences ─────────────────────────────────────────────
NOTES: dict[str, dict[str, str]] = {
    "grey.multi_annex": {
        "en": "the description matches {n} distinct Annex III categories ({cats}). Either the "
              "system does several things — each needing its own assessment — or the description "
              "is too broad to classify.",
        "tr": "açıklama {n} farklı Annex III kategorisiyle eşleşiyor ({cats}). Ya sistem birden çok "
              "iş yapıyor — her biri kendi değerlendirmesini gerektirir — ya da açıklama "
              "sınıflandırılamayacak kadar geniş.",
    },
    "grey.annex_i_and_iii": {
        "en": "the system matches both Annex I product-safety legislation and an Annex III use "
              "case. Both routes lead to high risk, but the conformity-assessment procedure "
              "differs, and which one applies is a legal determination.",
        "tr": "sistem hem Annex I ürün güvenliği mevzuatıyla hem de bir Annex III kullanım senaryosuyla "
              "eşleşiyor. Her iki yol da yüksek riske çıkar, ancak uygunluk değerlendirme "
              "prosedürü farklıdır ve hangisinin geçerli olduğu hukuki bir tespittir.",
    },
    "grey.gpai": {
        "en": " The system is also a general-purpose AI model: Chapter V duties apply in addition "
              "to, not instead of, the high-risk obligations.",
        "tr": " Sistem aynı zamanda genel amaçlı bir yapay zekâ modelidir: Bölüm V yükümlülükleri "
              "yüksek risk yükümlülüklerinin yerine değil, onlara ek olarak uygulanır.",
    },
    "grey.sector_only": {
        "en": "'{sector}' is a sector where Annex III use cases concentrate, and the description "
              "given does not resolve whether this system performs one. This is not evidence of "
              "low risk — it is an unanswered question.",
        "tr": "'{sector}', Annex III kullanım senaryolarının yoğunlaştığı bir sektördür ve verilen "
              "açıklama bu sistemin böyle bir iş yapıp yapmadığını çözmüyor. Bu, düşük risk "
              "kanıtı değildir — yanıtlanmamış bir sorudur.",
    },
    "limit.minimal": {
        "en": "This verdict rests on no indicator matching, which is not the same as evidence of "
              "low risk. The lexicon is structural and recognises only what it has been taught. A "
              "minimal classification should be re-run whenever the use case changes.",
        "tr": "Bu karar hiçbir göstergenin eşleşmemesine dayanıyor; bu, düşük risk kanıtıyla aynı "
              "şey değildir. Sözlük yapısaldır ve yalnızca kendisine öğretileni tanır. Asgari "
              "sınıflandırma, kullanım senaryosu her değiştiğinde yeniden çalıştırılmalıdır.",
    },
    "limit.prohibited": {
        "en": "A prohibition match is a stop signal, not a legal conclusion. Art. 5 carries narrow "
              "exemptions this tool does not evaluate.",
        "tr": "Bir yasak eşleşmesi bir durdurma sinyalidir, hukuki bir sonuç değildir. Art. 5, bu "
              "aracın değerlendirmediği dar istisnalar içerir.",
    },
    "limit.no_eu_market": {
        "en": "The system was declared as not placed on the EU market. The classification below is "
              "still computed, but the Regulation's obligations attach only where Art. 2 scope is "
              "met — that determination is not made by this tool.",
        "tr": "Sistemin AB pazarına sunulmadığı beyan edildi. Aşağıdaki sınıflandırma yine de "
              "hesaplanır, ancak Tüzüğün yükümlülükleri yalnızca Art. 2 kapsamı karşılandığında "
              "doğar — bu tespit bu araç tarafından yapılmaz.",
    },
    "limit.provide_use_cases": {
        "en": "Provide concrete use cases to resolve this classification.",
        "tr": "Bu sınıflandırmayı çözmek için somut kullanım senaryoları sağlayın.",
    },
    "limit.no_baseline": {
        "en": "No baseline snapshot was supplied, so semantic drift was not measured. A single "
              "snapshot cannot show movement.",
        "tr": "Referans anlık görüntü verilmedi, bu nedenle anlamsal kayma ölçülmedi. Tek bir "
              "anlık görüntü hareket gösteremez.",
    },
    "limit.lexicon": {
        "en": "Detection is lexicon-based and English-first. A clean result means no listed term "
              "was matched — it is not evidence that the corpus is unbiased, and a non-English "
              "corpus will under-report on every dimension.",
        "tr": "Tespit sözlük tabanlıdır ve önce İngilizcedir. Temiz bir sonuç, listelenen hiçbir "
              "terimin eşleşmediği anlamına gelir — külliyatın önyargısız olduğunun kanıtı "
              "değildir ve İngilizce olmayan bir külliyat her boyutta eksik raporlanır.",
    },
    "limit.surface_terms": {
        "en": "Representation counts surface terms, not people. A corpus discussing a group "
              "without using its listed vocabulary is invisible to this measure.",
        "tr": "Temsil, insanları değil yüzey terimlerini sayar. Listelenen kelime dağarcığını "
              "kullanmadan bir gruptan söz eden bir külliyat bu ölçüm için görünmezdir.",
    },
    "limit.no_dimension_measured": {
        "en": "No dimension reached the measurement floor, so no Fairness Score was produced. "
              "This is an unmeasured corpus, not a fair one.",
        "tr": "Hiçbir boyut ölçüm alt sınırına ulaşmadı, bu yüzden Adillik Skoru üretilmedi. Bu, "
              "ölçülmemiş bir külliyattır, adil bir külliyat değil.",
    },
    "limit.vendor_seed": {
        "en": "Seed facts dated {as_of} were used. They are a prompt for what to verify, not a "
              "substitute for verification.",
        "tr": "{as_of} tarihli başlangıç bilgileri kullanıldı. Bunlar neyin doğrulanacağına dair "
              "bir hatırlatmadır, doğrulamanın yerine geçmez.",
    },
    "limit.vendor_unverified": {
        "en": "No customer-verified facts were supplied. This assessment reflects public "
              "documentation, which describes what a vendor offers — not what is configured on "
              "this account or written into this contract.",
        "tr": "Müşteri tarafından doğrulanmış bilgi sağlanmadı. Bu değerlendirme, bir satıcının "
              "neyi sunduğunu tarif eden kamuya açık dokümantasyonu yansıtır — bu hesapta neyin "
              "yapılandırıldığını ya da bu sözleşmede neyin yazdığını değil.",
    },
    "limit.vendor_unknowns": {
        "en": "{n} of {total} criteria could not be established. The score reflects that opacity "
              "by design — an unanswered question earns {credit} credit, not full credit and not "
              "zero — but a score computed mostly from unknowns describes the state of your "
              "information about this vendor more than it describes the vendor.",
        "tr": "{total} ölçütten {n} tanesi tespit edilemedi. Skor bu belirsizliği tasarım gereği "
              "yansıtır — yanıtsız bir soru tam puan da sıfır da değil, {credit} puan alır — ancak "
              "çoğunlukla bilinmeyenlerden hesaplanan bir skor, satıcıyı tarif etmekten çok bu "
              "satıcı hakkındaki bilginizin durumunu tarif eder.",
    },
    "bias.floor": {
        "en": "only {total} mention(s) across {groups} group(s); below the {floor}-mention / "
              "2-group floor needed to distinguish imbalance from absence",
        "tr": "{groups} grup genelinde yalnızca {total} anma; dengesizliği yokluktan ayırmak için "
              "gereken {floor}-anma / 2-grup alt sınırının altında",
    },
}


def note(key: str, locale: Locale = DEFAULT_LOCALE, **params: Any) -> str:
    entry = NOTES.get(key) or REASONING.get(key)
    if entry is None:
        return key
    text = entry.get(locale) or entry.get(DEFAULT_LOCALE, key)
    return text.format(**params) if params else text


def both(key: str, **params: Any) -> tuple[str, str]:
    """The same sentence in both languages, built at the same moment from the
    same values — so the two can never describe different findings."""
    return note(key, "en", **params), note(key, "tr", **params)


def finding_text(check: str, field: str, locale: Locale, fallback: str,
                 params: dict[str, Any] | None = None) -> str:
    """Localised `detail` or `remediation` for a check, or the module's own text.

    Falls back to `fallback` — the English string the module already wrote — when
    the catalogue has no entry or the parameters do not fit. Missing translation
    must degrade to a readable report, never to a KeyError in a compliance run.
    """
    if locale == DEFAULT_LOCALE:
        return fallback
    entry = FINDINGS.get(check.split(".")[0], {}).get(field)
    if not entry:
        return fallback
    template = entry.get(locale)
    if not template:
        return fallback
    try:
        return template.format(**(params or {}))
    except (KeyError, IndexError, ValueError):
        return fallback
