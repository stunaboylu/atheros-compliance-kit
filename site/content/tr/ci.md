# CI kapısı
> Bir değerlendirmeyi, mühendislerinizin kapatmadığı bir kontrole dönüştürmek.

# CI kapısı

Kimsenin uygulamadığı bir yönetişim sayısı çürür. Mühendislerin saygı duyduğu tek uygulama noktası derlemeyi başarısız kılandır — ve sürdürdükleri tek kapı, onlara yalan söylemeyendir.

## Yapılandırın

```yaml
# atheros.yml
audit_file: .atheros/audit_trail.jsonl
report_dir: .atheros/reports
locale: tr          # ya da en

fail_on:
  fairness_score_below: 70
  quality_score_below: 70
  vendor_score_below: 60
  drift_verdict_in: [shifted]
  risk_tier_in: [unacceptable]
  residency_verdict_in: [non_compliant]
  guard_blocks_above: 0
  chain_violation: true
```

`atheros-kit init --ci github` bu dosyayı ve çalışan bir iş akışını yazar. PyYAML bulunmayan bir temel kurulumda bunun yerine `atheros.json` yazar ve nedenini söyler — aracın sonra ayrıştırmayı reddettiği bir başlangıç yapılandırması, bozuk bir ilk beş dakikadır.

## Çalıştırın

```
atheros-kit ci gate        # 0 geçti · 1 başarısız · 2 hata
```

## İki kural

**Ölçülmemiş bir kontrol başarısızdır.** `None` skoru, ölçümün çalışmadığı ya da hesaplanamadığı anlamına gelir. Bunu geçer saymak, kapının tam da olmaması gereken anda — ölçümün kendisi bozulduğunda — yeşile dönmesi demektir.

**Atlanan her kontrol yazılır.** Bir modül yapılandırılmadıysa özet onu adlandırır. Neyi kontrol etmediğini gizleyen bir kapı tam kapsam gibi okunur ve özeti okuyan kişi, genellikle farkı bilemeyecek kişidir.

```
uyum kapısı — BAŞARISIZ
  ⨯ fairness_score      başarısız  0.0    0.0 < 70
  ⨯ quality_score       başarısız  24.5   24.5 < 70
  ? corpus_drift        ölçülmedi         referans verilmedi
  – vendor              atlandı           modül yapılandırılmamış
  ✓ audit_chain         geçti      sağlam
```

## GitHub Actions

Üretilen iş akışı Kit'i kurar (saniyeler — çekirdeğin bağımlılığı yoktur), kapıyı çalıştırır, özeti pull request'e yorumlar ve kanıtı 90 günlük saklamayla yükler — **iş başarısız olduğunda bile**. Yalnızca başarıda var olan bir çıktı, kimsenin okumadığı bir çıktıdır.

API anahtarı gerekmez. `GEMINI_API_KEY` ya da `OPENAI_API_KEY`'i yalnızca isteğe bağlı anlatı katmanını istiyorsanız ayarlayın; her sayı iki durumda da deterministik üretilir.

## GitLab CI

Aynı şablon dizininde gelir. Aynı sözleşme, `artifacts: when: always` ve raporun merge request bileşeninde gösterilmesi.

## Referanslar

Kayma iki anlık görüntü gerektirir. Kodun yanında bir referans dışa aktarımı tutun ve `--baseline` ile geçirin; referans olmadan kapı kaymayı kararlı değil, **atlandı** olarak bildirir.

Bir anlık görüntüyü yeni referans yapmayı yalnızca değişiklik kasıtlıysa yapın. Sessizce yükseltmek kaymayı kalıcı olarak gizler.

## Önce neyi ölçmeli

Bu sırayla benimseyin — her adım bir sonrakini hak ettirir:

- **Koruma sarmalayıcısı.** İlk gün, tamamen mühendislik gerekçesiyle: kişisel veri sızdırma, enjekte edilme. Uyum argümanı gerekmez.
- **`chain_violation` ve `risk_tier_in` üzerinde kapı.** Ucuz ve asla yanlış alarm vermez.
- **Külliyat denetimi.** Biri Art. 10'u sorduğunda.
- **Satıcı değerlendirmeleri.** Tedarik ilk anketi gönderdiğinde.
