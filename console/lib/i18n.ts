/**
 * Console UI strings.
 *
 * The Kit's own report already carries both languages for every finding, limit
 * and remediation (`detail` / `detail_tr`), so switching language here re-renders
 * instantly and offline — no refetch, and a static export toggles just as well as
 * the dev server.
 *
 * What this file translates is the CHROME: headings, labels, banners. Article
 * citations, check identifiers, enum values and hashes are never translated,
 * matching `atheros_kit.core.i18n` — a bilingual evidence pack in which the same
 * article appears under two spellings cannot be cross-referenced.
 */
export type Locale = 'en' | 'tr';

type Entry = { en: string; tr: string };

const S = {
  'app.title': { en: 'AtherosAI Compliance Console', tr: 'AtherosAI Uyum Konsolu' },
  'app.subtitle': {
    en: 'Read-only. It renders what the Kit emitted; it cannot reach your systems.',
    tr: 'Salt okunur. Kit’in ürettiğini gösterir; sistemlerinize erişemez.',
  },
  'nav.overview': { en: 'Overview', tr: 'Genel bakış' },
  'nav.risk': { en: 'Risk classification', tr: 'Risk sınıflandırması' },
  'nav.rag': { en: 'RAG quality', tr: 'RAG kalitesi' },
  'nav.guard': { en: 'Guard activity', tr: 'Koruma etkinliği' },
  'nav.vendor': { en: 'Vendor risk', tr: 'Satıcı riski' },
  'nav.ledger': { en: 'Ledger integrity', tr: 'Defter bütünlüğü' },

  'gate.title': { en: 'Compliance gate', tr: 'Uyum kapısı' },
  'gate.passed': { en: 'passed', tr: 'geçti' },
  'gate.failed': { en: 'failed', tr: 'başarısız' },
  'gate.checks': { en: 'Checks', tr: 'Kontroller' },
  'gate.run': { en: 'Run', tr: 'Çalışma' },
  'gate.result': { en: 'Result', tr: 'Sonuç' },
  'gate.session': { en: 'Session', tr: 'Oturum' },
  'gate.schema': { en: 'Schema', tr: 'Şema' },
  'gate.artefacts': { en: 'Artefacts', tr: 'Çıktılar' },
  'gate.modules': { en: 'Modules reporting', tr: 'Rapor veren modüller' },
  'gate.unmeasured.title': {
    en: 'Unmeasured checks fail by design',
    tr: 'Ölçülmeyen kontroller tasarım gereği başarısız olur',
  },
  'gate.unmeasured.body': {
    en: 'checks could not be computed. An unmeasured check is not a pass — a gate that goes '
      + 'green when the measurement breaks is worse than no gate.',
    tr: 'kontrol hesaplanamadı. Ölçülmemiş bir kontrol geçer sayılmaz — ölçüm bozulduğunda '
      + 'yeşile dönen bir kapı, hiç kapı olmamasından kötüdür.',
  },
  'gate.skipped.title': { en: 'checks did not run', tr: 'kontrol çalışmadı' },
  'gate.skipped.body': {
    en: 'This gate covers less than its check list suggests:',
    tr: 'Bu kapı, kontrol listesinin ima ettiğinden azını kapsıyor:',
  },
  'gate.source': { en: 'Report source', tr: 'Rapor kaynağı' },
  'demo.title': {
    en: 'Sample data — nothing here is real',
    tr: 'Örnek veri — buradaki hiçbir şey gerçek değil',
  },
  'demo.body': {
    en: 'This is the bundled demonstration report: a synthetic hiring corpus and an invented '
      + 'system called TalentFlow, produced by running the toolkit itself. No customer data '
      + 'reaches this page, and none can — the Console has no server, no database, and no way '
      + 'to fetch anything you have not pointed it at.',
    tr: 'Bu, pakete gömülü gösterim raporudur: sentetik bir işe alım külliyatı ve TalentFlow '
      + 'adında uydurma bir sistem; araç setinin kendisi çalıştırılarak üretilmiştir. Bu '
      + 'sayfaya hiçbir müşteri verisi ulaşmaz ve ulaşamaz — konsolun sunucusu, veritabanı ve '
      + 'kendisine göstermediğiniz bir şeyi getirme yolu yoktur.',
  },
  'gate.footer': {
    en: 'This Console renders reports the Kit emitted. It holds no connection to your models, '
      + 'your corpus, or your vendors, and nothing shown here left your CI to be computed.',
    tr: 'Bu konsol, Kit’in ürettiği raporları gösterir. Modellerinize, külliyatınıza ya da '
      + 'satıcılarınıza bağlantısı yoktur ve burada gösterilen hiçbir şey hesaplanmak için '
      + 'CI’nızdan çıkmamıştır.',
  },

  'stat.passed': { en: 'Passed', tr: 'Geçti' },
  'stat.failed': { en: 'Failed', tr: 'Başarısız' },
  'stat.unmeasured': { en: 'Unmeasured', tr: 'Ölçülmedi' },
  'stat.skipped': { en: 'Skipped', tr: 'Atlandı' },
  'export.json': { en: 'JSON', tr: 'JSON' },
  'export.markdown': { en: 'Markdown', tr: 'Markdown' },
  'export.print': { en: 'Print / PDF', tr: 'Yazdır / PDF' },
  'export.label': { en: 'Download', tr: 'İndir' },
  'export.note': {
    en: 'Files are produced in your browser from data already on this page. Nothing is uploaded, '
      + 'and no server is contacted.',
    tr: 'Dosyalar bu sayfadaki veriden tarayıcınızda üretilir. Hiçbir şey yüklenmez ve hiçbir '
      + 'sunucuya bağlanılmaz.',
  },
  'common.scores': { en: 'Scores', tr: 'Skorlar' },
  'common.findings': { en: 'Findings', tr: 'Bulgular' },
  'common.limits': { en: 'Limits of this assessment', tr: 'Bu değerlendirmenin sınırları' },
  'common.no_findings': {
    en: 'No findings were raised by the checks that ran.',
    tr: 'Çalışan kontroller herhangi bir bulgu üretmedi.',
  },
  'common.no_scores': { en: 'No scores in this report', tr: 'Bu raporda skor yok' },
  'common.remediation': { en: 'Remediation', tr: 'İyileştirme' },
  'common.evidence': { en: 'Evidence', tr: 'Kanıt' },
  'common.tap_remediation': { en: 'tap for remediation', tr: 'iyileştirme için dokunun' },
  'common.threshold': { en: 'threshold', tr: 'eşik' },
  'common.unmeasured_note': {
    en: 'Unmeasured. This is not a passing score — the measurement did not run or could not be '
      + 'computed.',
    tr: 'Ölçülmedi. Bu geçer bir skor değildir — ölçüm çalışmadı ya da hesaplanamadı.',
  },
  'common.unmeasured_does_not_pass': {
    en: 'unmeasured does not pass',
    tr: 'ölçülmemiş olmak geçer sayılmaz',
  },
  'common.pass': { en: 'pass', tr: 'geçti' },
  'common.fail': { en: 'FAIL', tr: 'BAŞARISIZ' },
  'common.degraded': { en: 'degraded', tr: 'düşürülmüş' },

  'band.good': { en: 'good', tr: 'iyi' },
  'band.watch': { en: 'watch', tr: 'izlenmeli' },
  'band.poor': { en: 'poor', tr: 'zayıf' },
  'band.critical': { en: 'critical', tr: 'kritik' },
  'band.unmeasured': { en: 'unmeasured', tr: 'ölçülmedi' },
  'severity.critical': { en: 'critical', tr: 'kritik' },
  'severity.high': { en: 'high', tr: 'yüksek' },
  'severity.medium': { en: 'medium', tr: 'orta' },
  'severity.low': { en: 'low', tr: 'düşük' },
  'severity.info': { en: 'info', tr: 'bilgi' },

  'risk.confidence': { en: 'confidence', tr: 'güven' },
  'risk.basis': { en: 'basis', tr: 'dayanak' },
  'risk.reasoning': { en: 'Reasoning', tr: 'Gerekçe' },
  'risk.articles': { en: 'Articles', tr: 'Maddeler' },
  'risk.annex': { en: 'Annex III categories', tr: 'Annex III kategorileri' },
  'risk.obligations': { en: 'Obligations', tr: 'Yükümlülükler' },
  'risk.obligations.note': {
    en: 'Each duty names the module that produces its evidence. This mapping is why the four '
      + 'modules are one product.',
    tr: 'Her yükümlülük, kanıtını üreten modülü adlandırır. Dört modülün tek bir ürün olmasının '
      + 'nedeni bu eşlemedir.',
  },
  'risk.grey.title': { en: 'Grey zone — this needs a human', tr: 'Gri bölge — insan gerekiyor' },
  'risk.no_indicator.title': {
    en: 'This verdict rests on nothing matching',
    tr: 'Bu karar hiçbir eşleşme olmamasına dayanıyor',
  },
  'risk.no_indicator.body': {
    en: 'No prohibited practice, Annex III use case, or transparency trigger was recognised in '
      + 'the description given. That is not the same as evidence of low risk — the lexicon is '
      + 'structural and recognises only what it has been taught.',
    tr: 'Verilen açıklamada yasaklanmış bir uygulama, Annex III kullanım senaryosu ya da '
      + 'şeffaflık tetikleyicisi tanınmadı. Bu, düşük risk kanıtıyla aynı şey değildir — sözlük '
      + 'yapısaldır ve yalnızca kendisine öğretileni tanır.',
  },
  'risk.sector_only.title': {
    en: 'An unanswered question, not a low-risk finding',
    tr: 'Yanıtlanmamış bir soru, düşük risk bulgusu değil',
  },
  'risk.sector_only.body': {
    en: 'The system sits in a sector where Annex III use cases concentrate, and the description '
      + 'given does not resolve whether it performs one. Supply concrete use cases to classify it.',
    tr: 'Sistem, Annex III kullanım senaryolarının yoğunlaştığı bir sektörde yer alıyor ve '
      + 'verilen açıklama böyle bir iş yapıp yapmadığını çözmüyor. Sınıflandırmak için somut '
      + 'kullanım senaryoları sağlayın.',
  },
  'risk.gpai': {
    en: 'General-purpose AI model duties (Chapter V)',
    tr: 'Genel amaçlı yapay zekâ modeli yükümlülükleri (Bölüm V)',
  },
  'risk.gpai.note': {
    en: 'These apply in addition to the tier above, not instead of it.',
    tr: 'Bunlar yukarıdaki seviyenin yerine değil, ona ek olarak uygulanır.',
  },
  'risk.footer': {
    en: 'This is an automated assessment. It is not a conformity assessment, not a '
      + 'certification, and not legal advice.',
    tr: 'Bu otomatik bir değerlendirmedir. Uygunluk değerlendirmesi, belgelendirme ya da hukuki '
      + 'tavsiye değildir.',
  },
  'risk.empty': {
    en: 'No classification in this report',
    tr: 'Bu raporda sınıflandırma yok',
  },
  'risk.empty.detail': {
    en: 'Run `atheros-kit euact classify --spec system.json` and pass the result to the gate.',
    tr: '`atheros-kit euact classify --spec system.json` çalıştırın ve sonucu kapıya verin.',
  },
  'risk.evidence_by': { en: 'evidence', tr: 'kanıt' },
  'risk.no_module': {
    en: 'no Kit module produces this',
    tr: 'bunu hiçbir Kit modülü üretmez',
  },

  'rag.fairness': { en: 'Fairness', tr: 'Adillik' },
  'rag.fairness_score': { en: 'fairness score', tr: 'adillik skoru' },
  'rag.quality': { en: 'Corpus quality', tr: 'Külliyat kalitesi' },
  'rag.quality_score': { en: 'quality score', tr: 'kalite skoru' },
  'rag.chunks_scanned': { en: 'chunks scanned', tr: 'parça tarandı' },
  'rag.bias_by_dimension': { en: 'Bias by dimension', tr: 'Boyuta göre önyargı' },
  'rag.unassessable': { en: 'unassessable', tr: 'değerlendirilemez' },
  'rag.unassessable.title': {
    en: 'dimensions could not be measured',
    tr: 'boyut ölçülemedi',
  },
  'rag.unassessable.body': {
    en: 'below the mention floor needed to distinguish imbalance from absence. The Fairness Score '
      + 'describes only the assessed dimensions, and silence is not fairness.',
    tr: 'dengesizliği yokluktan ayırmak için gereken anma alt sınırının altında. Adillik Skoru '
      + 'yalnızca değerlendirilen boyutları tarif eder ve sessizlik adillik değildir.',
  },
  'rag.drift': { en: 'Semantic drift', tr: 'Anlamsal kayma' },
  'rag.drift.not_measured': { en: 'Drift not measured', tr: 'Kayma ölçülmedi' },
  'rag.drift.no_baseline': {
    en: 'No baseline snapshot was supplied. A single snapshot cannot show movement.',
    tr: 'Referans anlık görüntü verilmedi. Tek bir anlık görüntü hareket gösteremez.',
  },
  'rag.negatively_framed': {
    en: 'described in measurably more negative language than the corpus mean. This is the bias '
      + 'that survives a representation audit.',
    tr: 'külliyat ortalamasından ölçülebilir biçimde daha olumsuz bir dille anlatılmış. Bu, '
      + 'temsil denetiminden sağ çıkan önyargıdır.',
  },
  'rag.remediation.note': {
    en: 'Ordered by leverage. Nothing here runs automatically — the Kit’s connection to your '
      + 'corpus is read-only by design.',
    tr: 'Kaldıraç sırasına göre. Buradaki hiçbir şey otomatik çalışmaz — Kit’in külliyatınıza '
      + 'bağlantısı tasarım gereği salt okunurdur.',
  },
  'rag.empty': { en: 'No corpus audit in this report', tr: 'Bu raporda külliyat denetimi yok' },

  'guard.title': { en: 'Guard activity', tr: 'Koruma etkinliği' },
  'guard.no_values.title': { en: 'Values are never recorded', tr: 'Değerler asla kaydedilmez' },
  'guard.no_values.body': {
    en: 'Everything below is a class and a count. The ledger holds no prompt text, no response '
      + 'text, and no detected value — a compliance record that stores the PII it found is the '
      + 'failure it exists to prevent.',
    tr: 'Aşağıdaki her şey bir sınıf ve bir sayıdır. Defter hiçbir istem metni, yanıt metni ya da '
      + 'tespit edilmiş değer tutmaz — bulduğu kişisel veriyi saklayan bir uyum kaydı, tam da '
      + 'önlemek için var olduğu başarısızlıktır.',
  },
  'guard.invocations': { en: 'Invocations', tr: 'Çağrılar' },
  'guard.tokens': { en: 'Tokens', tr: 'Token' },
  'guard.blocked': { en: 'Blocked', tr: 'Engellenen' },
  'guard.degraded': { en: 'Degraded', tr: 'Düşürülen' },
  'guard.entities_masked': { en: 'Entities masked', tr: 'Maskelenen varlık' },
  'guard.masked_classes': { en: 'Masked entity classes', tr: 'Maskelenen varlık sınıfları' },
  'guard.signatures': { en: 'Signatures triggered', tr: 'Tetiklenen imzalar' },
  'guard.governance': { en: 'Token governance', tr: 'Token yönetişimi' },
  'guard.empty': { en: 'No guard session in this report', tr: 'Bu raporda koruma oturumu yok' },

  'vendor.residency': { en: 'Data residency', tr: 'Veri yerleşimi' },
  'vendor.optout': { en: 'Training opt-out', tr: 'Eğitimden çıkma' },
  'vendor.optout.note': {
    en: 'Available, enabled and contractual are three different facts.',
    tr: 'Mevcut, etkin ve sözleşmesel üç farklı olgudur.',
  },
  'vendor.criteria': { en: 'Criteria', tr: 'Ölçütler' },
  'vendor.by_group': { en: 'Score by group', tr: 'Gruba göre skor' },
  'vendor.score': { en: 'vendor score', tr: 'satıcı skoru' },
  'vendor.empty': { en: 'No vendor assessment in this report', tr: 'Bu raporda satıcı değerlendirmesi yok' },
  'vendor.yes': { en: 'yes', tr: 'evet' },
  'vendor.no': { en: 'no', tr: 'hayır' },
  'vendor.not_established': { en: 'not established', tr: 'tespit edilemedi' },
  'vendor.available': { en: 'Available', tr: 'Mevcut' },
  'vendor.enabled': { en: 'Enabled on this account', tr: 'Bu hesapta etkin' },
  'vendor.contractual': { en: 'Contractually committed', tr: 'Sözleşmesel taahhüt' },
  'vendor.zdr': { en: 'Zero data retention', tr: 'Sıfır veri saklama' },

  'ledger.title': { en: 'Ledger integrity', tr: 'Defter bütünlüğü' },
  'ledger.subtitle': {
    en: 'Every module writes here. ISO/IEC 42001 §9.1 — monitoring, measurement, analysis and '
      + 'evaluation.',
    tr: 'Her modül buraya yazar. ISO/IEC 42001 §9.1 — izleme, ölçme, analiz ve değerlendirme.',
  },
  'ledger.chain': { en: 'Chain', tr: 'Zincir' },
  'ledger.entries': { en: 'entries', tr: 'kayıt' },
  'ledger.intact': { en: 'intact', tr: 'sağlam' },
  'ledger.violations': { en: 'violation(s)', tr: 'ihlal' },
  'ledger.unverified': { en: 'unverified', tr: 'doğrulanmadı' },
  'ledger.verifying': { en: 'verifying', tr: 'doğrulanıyor' },
  'ledger.reverify': { en: 'Re-verify', tr: 'Yeniden doğrula' },
  'ledger.independent': {
    en: 'This check recomputes every digest here in the browser, independently of the Python '
      + 'implementation that wrote them. A verifier sharing code with the writer can only prove '
      + 'they agree with each other.',
    tr: 'Bu kontrol, her özeti tarayıcıda, onları yazan Python uygulamasından bağımsız olarak '
      + 'yeniden hesaplar. Yazanla kodu paylaşan bir doğrulayıcı yalnızca birbirleriyle '
      + 'anlaştıklarını kanıtlayabilir.',
  },
  'ledger.meaning.title': {
    en: "What 'intact' means, and what it does not",
    tr: "'Sağlam'ın anlamı ve anlamı olmayan",
  },
  'ledger.meaning.body': {
    en: 'Every entry links to its predecessor and every digest recomputes. That makes deletion, '
      + 'reordering and editing detectable. It does not make the contents true — the chain '
      + 'attests to what was recorded, not to whether the assessment behind it was correct.',
    tr: 'Her kayıt kendinden öncekine bağlanır ve her özet yeniden hesaplanır. Bu, silme, yeniden '
      + 'sıralama ve düzenlemeyi tespit edilebilir kılar. İçeriği doğru kılmaz — zincir, neyin '
      + 'kaydedildiğine tanıklık eder, arkasındaki değerlendirmenin doğru olup olmadığına değil.',
  },
  'ledger.all': { en: 'all', tr: 'tümü' },

  'notfound.title': { en: 'Not found', tr: 'Bulunamadı' },
  'notfound.body': {
    en: 'That screen does not exist in this Console.',
    tr: 'Bu konsolda böyle bir ekran yok.',
  },
  'notfound.back': { en: 'Back to the overview', tr: 'Genel bakışa dön' },
} satisfies Record<string, Entry>;

export type Key = keyof typeof S;

export function t(key: Key, locale: Locale): string {
  return S[key][locale];
}

/**
 * A finding's detail in the requested language.
 *
 * The Kit emits `detail_tr` alongside `detail` on every finding, so this is a
 * field pick rather than a lookup — and a report generated before Turkish
 * existed still renders, in English, instead of showing an empty row.
 */
export function localised<T extends { detail: string; detail_tr?: string }>(
  item: T,
  locale: Locale,
): string {
  return locale === 'tr' && item.detail_tr ? item.detail_tr : item.detail;
}

export function localisedRemediation<
  T extends { remediation: string | null; remediation_tr?: string | null },
>(item: T, locale: Locale): string | null {
  return locale === 'tr' && item.remediation_tr ? item.remediation_tr : item.remediation;
}
