"""Versioned EU AI Act vocabulary — regulation content as DATA, not code.

A law change must be a version bump and a data edit, never a code change. That
is why the indicator lists, the article map and the obligation catalogue all
live here behind `REGULATION_VERSION`, and why every classification records the
version it was produced under. Two assessments of the same system that disagree
are only explicable if each says which text it was reading.

Sourced from Regulation (EU) 2024/1689. Article numbering follows the published
Official Journal text: transparency obligations for providers and deployers of
certain AI systems are **Article 50** (they were Article 52 in the 2021 proposal
and in a great deal of secondary writing, which is why the alias is recorded
explicitly below rather than left for a reader to trip over).
"""
from __future__ import annotations

REGULATION_VERSION = "EU-2024/1689:2024-07-12"

#: Article numbers that moved between the proposal and the final text. Kept so a
#: customer citing the old number in their own documentation can be matched.
ARTICLE_ALIASES = {"Art. 52": "Art. 50", "Art. 52a": "Art. 50"}

# ── Article 5 — prohibited practices ─────────────────────────────────────────
UNACCEPTABLE_INDICATORS: dict[str, list[str]] = {
    "subliminal_manipulation": [
        "subliminal", "manipulative technique", "deceptive technique",
        "exploit vulnerability", "behavioural manipulation",
    ],
    "vulnerability_exploitation": [
        "exploit age", "exploit disability", "target children", "vulnerable group targeting",
    ],
    "social_scoring": [
        "social score", "social scoring", "citizen score", "trustworthiness score",
        "social credit",
    ],
    "predictive_policing_individual": [
        "predict criminal", "criminal prediction", "predictive policing", "recidivism prediction",
        "crime likelihood",
    ],
    "facial_scraping": [
        "facial recognition database", "scrape facial", "untargeted scraping",
        "facial image scraping",
    ],
    "emotion_workplace_education": [
        "emotion recognition workplace", "emotion detection employee",
        "emotion recognition school", "student emotion",
    ],
    "biometric_categorisation_sensitive": [
        "infer race", "infer ethnicity", "infer sexual orientation", "infer political opinion",
        "infer religious belief", "biometric categorisation",
    ],
    "realtime_remote_biometric_public": [
        "real-time remote biometric", "live facial recognition public",
        "realtime biometric identification public",
    ],
}

# ── Annex III — high-risk use cases ──────────────────────────────────────────
ANNEX_III_CATEGORIES: dict[str, list[str]] = {
    "1. Biometrics": [
        "biometric identification", "biometric verification", "face recognition",
        "fingerprint", "iris scan", "voice identification", "gait recognition",
    ],
    "2. Critical infrastructure": [
        "critical infrastructure", "traffic management", "water supply", "gas supply",
        "electricity supply", "heating supply", "digital infrastructure safety",
    ],
    "3. Education and vocational training": [
        "student admission", "exam scoring", "exam proctoring", "grading",
        "educational assessment", "learning outcome prediction", "student evaluation",
        "admission decision", "school placement",
    ],
    "4. Employment and worker management": [
        "cv screening", "resume screening", "candidate ranking", "recruitment",
        "hiring decision", "job applicant", "promotion decision", "termination decision",
        "task allocation", "worker monitoring", "performance evaluation", "employee evaluation",
    ],
    "5. Essential services and benefits": [
        "credit scoring", "creditworthiness", "loan approval", "loan decision",
        "insurance pricing", "life insurance", "health insurance risk",
        "public benefit", "social benefit eligibility", "emergency dispatch", "triage",
    ],
    "6. Law enforcement": [
        "law enforcement", "polygraph", "evidence reliability", "crime analytics",
        "criminal investigation", "victim risk assessment",
    ],
    "7. Migration, asylum and border control": [
        "asylum application", "visa application", "border control", "migration",
        "immigration risk", "residence permit",
    ],
    "8. Administration of justice": [
        "judicial decision", "court decision support", "legal reasoning assistance",
        "sentencing", "democratic process", "election influence",
    ],
}

#: Annex I — products already covered by Union harmonisation legislation. High-risk
#: under Art. 6(1) by a different route than Annex III, and the distinction matters:
#: the conformity assessment runs through the SECTORAL regime, not the AI Act's own.
ANNEX_I_PRODUCTS: dict[str, list[str]] = {
    "machinery": ["machinery safety", "industrial machine control"],
    "medical_device": ["medical device", "diagnosis support", "clinical decision support",
                       "in vitro diagnostic", "patient triage"],
    "vehicle": ["autonomous driving", "vehicle safety", "adas", "driver assistance"],
    "aviation": ["aircraft system", "air traffic"],
    "toys": ["toy safety", "children's toy"],
    "lifts": ["lift control", "elevator control"],
    "radio_equipment": ["radio equipment"],
}

# ── Article 50 — transparency obligations ────────────────────────────────────
LIMITED_RISK_INDICATORS: dict[str, list[str]] = {
    "human_interaction": ["chatbot", "conversational agent", "virtual assistant",
                          "customer support bot", "interacts with humans"],
    "synthetic_content": ["generates text", "generates image", "generates video",
                          "generates audio", "synthetic media", "generative"],
    "deepfake": ["deepfake", "face swap", "voice cloning", "synthetic person"],
    "emotion_recognition": ["emotion recognition", "sentiment of individuals", "affect detection"],
    "biometric_categorisation": ["biometric categorisation", "demographic inference"],
}

#: Sectors where deployment alone raises the prior, independent of use-case text.
#: A high-risk sector is not a classification on its own — it is a reason to look
#: harder, which is why it contributes to the tier only alongside a use case and
#: otherwise raises a grey zone.
HIGH_RISK_SECTORS = {
    "healthcare", "health", "finance", "fintech", "banking", "insurance",
    "employment", "hr", "recruitment", "education", "law_enforcement", "justice",
    "migration", "critical_infrastructure", "energy", "utilities",
}

# ── Obligations per tier ─────────────────────────────────────────────────────
# `evidence_source` names the Kit module that can actually produce the artefact.
# This is the spine that connects a legal duty to a thing an engineer can run,
# and it is the reason the four modules are one product rather than four.
OBLIGATIONS: dict[str, list[dict[str, str]]] = {
    "unacceptable": [
        {"article": "Art. 5", "duty": "Cease placing on the market, putting into service, or using this practice.",
         "duty_tr": "Bu uygulamanın piyasaya sürülmesini, hizmete sunulmasını veya kullanılmasını durdurun.",
         "evidence_source": "—", "note": "Prohibited. No compliance path exists; the design must change."},
    ],
    "high": [
        {"article": "Art. 9", "duty": "Establish, document and maintain a risk-management system across the lifecycle.",
         "duty_tr": "Yaşam döngüsü boyunca bir risk yönetim sistemi kurun, belgeleyin ve sürdürün.",
         "evidence_source": "euact.dossier"},
        {"article": "Art. 10", "duty": "Data governance: relevance, representativeness, and examination for bias in training, validation and testing data.",
         "duty_tr": "Veri yönetişimi: eğitim, doğrulama ve test verilerinde ilgililik, temsil edicilik ve önyargı incelemesi.",
         "evidence_source": "rag.bias + rag.quality"},
        {"article": "Art. 11 + Annex IV", "duty": "Draw up technical documentation before placing on the market and keep it up to date.",
         "duty_tr": "Piyasaya sürmeden önce teknik dokümantasyonu hazırlayın ve güncel tutun.",
         "evidence_source": "euact.dossier"},
        {"article": "Art. 12", "duty": "Automatic recording of events (logs) over the system's lifetime.",
         "duty_tr": "Sistemin ömrü boyunca olayların otomatik olarak kaydedilmesi.",
         "evidence_source": "core.audit + guard.ledger"},
        {"article": "Art. 13", "duty": "Design for transparency: instructions for use enabling deployers to interpret output.",
         "duty_tr": "Şeffaflık için tasarım: dağıtıcıların çıktıyı yorumlamasını sağlayan kullanım talimatları.",
         "evidence_source": "euact.dossier"},
        {"article": "Art. 14", "duty": "Enable effective human oversight, including the ability to disregard or reverse output.",
         "duty_tr": "Çıktıyı göz ardı etme veya geri alma yeteneği dâhil, etkili insan gözetimini mümkün kılın.",
         "evidence_source": "guard.fallback"},
        {"article": "Art. 15", "duty": "Appropriate accuracy, robustness and cybersecurity, including resilience to prompt injection and data poisoning.",
         "duty_tr": "İstem enjeksiyonu ve veri zehirlenmesine dayanıklılık dâhil uygun doğruluk, sağlamlık ve siber güvenlik.",
         "evidence_source": "guard.injection"},
        {"article": "Art. 17", "duty": "Quality-management system covering the above.",
         "duty_tr": "Yukarıdakileri kapsayan bir kalite yönetim sistemi.",
         "evidence_source": "cicd.gate"},
        {"article": "Art. 26", "duty": "Deployer duties: use per instructions, ensure input relevance, monitor and retain logs.",
         "duty_tr": "Dağıtıcı yükümlülükleri: talimatlara uygun kullanım, girdi ilgililiğinin sağlanması, izleme ve kayıtların saklanması.",
         "evidence_source": "guard.ledger"},
        {"article": "Art. 27", "duty": "Fundamental-rights impact assessment (public bodies and certain deployers).",
         "duty_tr": "Temel haklar etki değerlendirmesi (kamu kurumları ve belirli dağıtıcılar).",
         "evidence_source": "euact.dossier"},
    ],
    "limited": [
        {"article": "Art. 50(1)", "duty": "Inform natural persons that they are interacting with an AI system.",
         "duty_tr": "Gerçek kişileri, bir yapay zekâ sistemiyle etkileşimde olduklarına dair bilgilendirin.",
         "evidence_source": "euact.transparency"},
        {"article": "Art. 50(2)", "duty": "Mark synthetic content in a machine-readable format as artificially generated.",
         "duty_tr": "Sentetik içeriği yapay olarak üretilmiş şekilde makine tarafından okunabilir biçimde işaretleyin.",
         "evidence_source": "euact.transparency"},
        {"article": "Art. 50(3)", "duty": "Disclose emotion-recognition or biometric-categorisation to exposed persons.",
         "duty_tr": "Duygu tanıma veya biyometrik sınıflandırmayı maruz kalan kişilere açıklayın.",
         "evidence_source": "euact.transparency"},
        {"article": "Art. 50(4)", "duty": "Disclose deep-fake content as artificially generated or manipulated.",
         "duty_tr": "Derin sahte içeriği yapay olarak üretilmiş veya değiştirilmiş olarak açıklayın.",
         "evidence_source": "euact.transparency"},
    ],
    "minimal": [
        {"article": "Art. 4", "duty": "Ensure a sufficient level of AI literacy among staff operating the system.",
         "duty_tr": "Sistemi işleten personel arasında yeterli düzeyde yapay zekâ okuryazarlığı sağlayın.",
         "evidence_source": "—"},
        {"article": "—", "duty": "Voluntary codes of conduct (Art. 95). No mandatory obligations attach at this tier.",
         "duty_tr": "Gönüllü davranış kuralları (Art. 95). Bu seviyede zorunlu bir yükümlülük doğmaz.",
         "evidence_source": "—"},
    ],
}

#: General-purpose AI model duties (Chapter V) — orthogonal to the risk tier of
#: any system built on it. A team is frequently subject to both, and treating
#: them as alternatives is the most common classification error in the wild.
GPAI_OBLIGATIONS = [
    {"article": "Art. 53", "duty": "Technical documentation, information for downstream providers, copyright policy, training-data summary.",
         "duty_tr": "Teknik dokümantasyon, alt sağlayıcılara bilgi, telif hakkı politikası ve eğitim verisi özeti.",
     "evidence_source": "euact.dossier"},
    {"article": "Art. 55", "duty": "Systemic-risk models (>10^25 FLOP): model evaluation, adversarial testing, incident reporting, cybersecurity.",
         "duty_tr": "Sistemik riskli modeller (>10^25 FLOP): model değerlendirmesi, çekişmeli test, olay bildirimi, siber güvenlik.",
     "evidence_source": "guard.injection"},
]


def normalise_article(article: str) -> str:
    """Map a proposal-era article number onto the enacted one."""
    return ARTICLE_ALIASES.get(article.strip(), article.strip())


def find_indicators(subject: str, vocabulary: dict[str, list[str]]) -> dict[str, list[str]]:
    """Category → matched indicators, for every category with a hit.

    One matcher, used by the classifier, the dossier gap check and the CI gate.
    When this was reimplemented per call site the copies drifted — one normalised
    underscores and matched "credit_scoring", the other did not — and the same
    system classified differently depending on which door it came through.
    """
    hay = " ".join((subject or "").lower().replace("_", " ").replace("-", " ").split())
    out: dict[str, list[str]] = {}
    for category, indicators in vocabulary.items():
        hits = [ind for ind in indicators if ind.lower().replace("_", " ") in hay]
        if hits:
            out[category] = hits
    return out
