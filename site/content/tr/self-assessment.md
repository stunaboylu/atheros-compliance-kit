# Kendi uyum raporumuz
> AtherosAI Compliance Kit kendi üzerinde çalıştırıldı: EU AI Act seviyesi, %33 Annex IV tamlığı, bilerek kırmızı bırakılmış bir kontrol — düzeltilmeden yayımlandı.

# Öz-değerlendirme — AtherosAI Compliance Kit

_`scripts/self_assessment.py` tarafından **1.0.1** sürümüne karşı, `EU-2024/1689:2024-07-12` mevzuat sürümüyle üretildi._

Bu ürünü kendi üzerinde çalıştırıp sonucu boşluklarıyla birlikte yayımlıyoruz. Satıcısı kendi değerlendirmesini üretemeyen bir uyum aracı, kimsenin satın almaması gereken bir araçtır.

**Buradaki hiçbir şey ayarlanmadı.** Aşağıdaki sistem açıklaması, iyi puan alan değil teknik dosyaya girecek olandır — ve Modül 1, sentetik bir külliyatla beslenmek yerine atlandı, çünkü hiçbir anlamı olmayan dolu bir satır, bu ürünün yerine geçmek için var olduğu tiyatronun ta kendisidir.

---

## EU AI Act kapsamında biz neyiz

**Seviye: `minimal`** · güven 0.60 · dayanak `no_indicator_matched`

**Gerekçe**

- verilen açıklamada yasaklanmış bir uygulama, Annex I ürünü, Annex III kullanım senaryosu ya da Art. 50 şeffaflık tetikleyicisi tanınmadı

Kit deterministik bir analiz kütüphanesidir. Hiçbir gerçek kişi hakkında karar vermez, kimseyi sıralamaz, hiçbir şey verip almaz — dolayısıyla hiçbir Annex III kullanım senaryosu bağlanmaz. Genel amaçlı bir yapay zekâ modeli değildir ve isteğe bağlı anlatı katmanı varsayılan olarak kapalıdır, yani gönderilen yapılandırma hiçbir Art. 50 şeffaflık yükümlülüğü tetiklemez.

**Bu kararın anlamı OLMAYAN şey.** Aracın kendi sınıflandırması hakkında yazdırdığı sınırlar:

> - Bu karar hiçbir göstergenin eşleşmemesine dayanıyor; bu, düşük risk kanıtıyla aynı şey değildir. Sözlük yapısaldır ve yalnızca kendisine öğretileni tanır. Asgari sınıflandırma, kullanım senaryosu her değiştiğinde yeniden çalıştırılmalıdır.

Müşterilerimizin sistemleri sıklıkla yüksek risklidir. Bizimki değil, ve ayrım ürünün kendisidir: Kit, ihtiyacı olan sistemler hakkında kanıt üretirken kendisi öyle bir sistem hâline gelmez.

## Kendi Annex IV dokümantasyonumuz

Tamlık: **%33** — 9 bölümden 6 tanesi eksik ya da kısmi.

| Annex IV | Bölüm | Kapsam |
|---|---|---|
| Annex IV(1) | Yapay zekâ sisteminin genel tanımı | **karşılandı** |
| Annex IV(2)(a-b) | Geliştirme süreci ve sistem mimarisi | **karşılandı** |
| Annex IV(2)(d) | Veri ve veri yönetişimi | **eksik** |
| Annex IV(2)(e) | İnsan gözetimi tedbirleri | **eksik** |
| Annex IV(2)(g) | Doğruluk, sağlamlık ve metrikler | **eksik** |
| Annex IV(3) | Risk yönetim sistemi | **eksik** |
| Annex IV(4) | Yaşam döngüsü değişiklikleri | **eksik** |
| Annex IV(5) | Uygulanan uyumlaştırılmış standartlar | **eksik** |
| Annex IV(8-9) | Piyasaya arz sonrası izleme ve kayıt | **karşılandı** |

`minimal` riskli bir sistemiz, yani Art. 11 bu dosyayı tutmamızı zorunlu kılmıyor. Yine de üretiyor ve eksik hâliyle yayımlıyoruz — çünkü yukarıdaki sayı dürüst olanı, ve aracın satıldığı davranışı gösteriyor: **kanıt bir bölümü kısmi yapar, asla karşılanmış değil.** Dokuz bölümün hepsi için inandırıcı metin üreten bir üretici, tam görünen ama tam olmayan bir belge çıkarır.

## Kendi korumalarımız

| | |
|---|---|
| Çağrı | 2 |
| Engellenen | 1 |
| Düşürülen | 1 |
| Maskelenen sınıflar | EMAIL |
| Tetiklenen imzalar | instruction_override, verdict_override |
| Yanıtlayan | primary: 1, static: 1 |

İkinci öz-test istemi, kendi sarmalayıcımıza yapılan bir enjeksiyon denemesidir. Engellendi, hiç token harcanmadı ve engelleme zincire yazıldı.

## Kendi tedarikçilerimiz

Kit'in isteğe bağlı anlatı katmanı bu sağlayıcılara ulaşabilir. **Varsayılan olarak kapalıdır** — gönderilen yapılandırma `none:deterministic`, yani varsayılan bir kurulum hiçbir yere hiçbir şey göndermez. Bu değerlendirmeler, katmanı açan bir müşterinin neyi üstlendiğini tarif eder.

| Sağlayıcı | Skor | Yerleşim | Eğitimden çıkma | Tespit edilemeyen ölçüt |
|---|---:|---|---|---:|
| Google Cloud Vertex AI | 98.3 | requires_scc | available_not_evidenced | 0 |
| OpenAI | 83.3 | requires_scc | available_not_evidenced | 1 |

Kendi kaydımızın kendi bilgilerini 180 gün sonra eski olarak işaretlediğine ve bunu burada da yaptığına dikkat edin. Bu, aracın çalışmasıdır, raporun başarısızlığı değil.

## Kendi defterimiz

**sağlam** — her özet yeniden hesaplandı.

## Kapı, kendi üzerimizde

## AtherosAI uyum kapısı — BAŞARISIZ

| | Kontrol | Değer | Eşik | Ayrıntı |
|---|---|---|---|---|
| ⏭️ | `rag_audit` | — | — | module not configured |
| ✅ | `eu_ai_act_tier` | minimal | ['unacceptable'] |  |
| ✅ | `vendor_score.google_vertex` | 98.3 | 60 |  |
| ✅ | `residency.google_vertex` | requires_scc | ['non_compliant'] |  |
| ✅ | `vendor_score.openai` | 83.3 | 60 |  |
| ✅ | `residency.openai` | requires_scc | ['non_compliant'] |  |
| ❌ | `guard_blocks` | 1 | 0 | 1 blocked invocation(s) exceed the configured cap of 0 |
| ✅ | `audit_chain` | intact | intact |  |

> **1 kontrol çalışmadı.** Bu kapı, kontrol listesinin ima ettiğinden daha azını kapsıyor: rag_audit.

_AtherosAI Compliance Kit tarafından üretilmiştir._

> **`guard_blocks` neden kırmızı.** Öz-test, kendi sarmalayıcımıza bilerek bir enjeksiyon denemesi gönderiyor ve yapılandırılmış eşik sıfır engelleme. Kapı tam olarak olanı bildiriyor. Raporu yeşile çevirmek için eşiği yükseltmek yerine kırmızı bırakıyoruz — kapı geçene kadar ayarlanmış bir eşik, hiçbir şey ölçmeyen bir eşiktir.

## Bu değerlendirmenin tespit etmediği şeyler

- **Modül 1 çalışmadı.** Kit'in RAG külliyatı yok, denetlenecek bir şey yoktu. Kapı bunu satırı gizlemek yerine atlanmış bir kontrol olarak yazdırıyor.
- **Sınıflandırma yapısaldır.** Kendimiz hakkında yazdığımız bir açıklamaya uygulanmış, kendisine öğretileni tanıyan bir sözlüğe dayanır.
- **Sağlam bir zincir neyin kaydedildiğine tanıklık eder**, kayıtların arkasındaki değerlendirmelerin doğru olup olmadığına değil.
- **Bu bir öz-değerlendirmedir.** Bağımsız güvence değildir. Bağımsız güvence, üzerinde başka bir imza olan başka bir üründür ve ikisini karıştırmak, müşterilerimize yapmayın dediğimiz şeydir.

---

_Yeniden üretin: `python scripts/self_assessment.py`. Ağ yok, API anahtarı yok, bir saniyenin altında. Her CI derlemesinde çalışır ve commit'li kopya bayatlamışsa derleme başarısız olur._