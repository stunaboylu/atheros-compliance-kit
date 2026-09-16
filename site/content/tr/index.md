# İhtiyacı olan sistemin kendisinin ürettiği uyum kanıtı
> EU AI Act kanıtlarını ve {{iso_clause_count}} adı konmuş ISO/IEC 42001 maddesi için kayıtları kendi kod tabanınızın ve CI'nızın içinden üreten kurumsal bir Python araç seti — önyargı skorları, kişisel veri maskeleme kayıtları, risk sınıflandırmaları, üçüncü taraf satıcı değerlendirmeleri.

# İhtiyacı olan sistemin kendisinin ürettiği uyum kanıtı

CI'nız zaten testlerinizi çalıştırıyor. Artık Art. 10 kanıtınızı da çalıştırıyor.

**Kod tabanınızın ve CI'nızın içinde** çalışan, yapay zekâ yönetişiminin istediği çıktıları otomatik olarak, zincir özetli biçimde ve verileriniz süreçten çıkmadan üreten kurumsal bir Python araç seti.

```
pip install atheros-compliance-kit
atheros-kit init --ci github
```

:::<p><a class="cta" href="quickstart.html">Beş dakikalık hızlı başlangıç</a><a class="cta ghost" href="honesty.html">Neyi ölçemediğini neden söyler</a><a class="cta ghost" href="../demo/">Gerçek bir raporu görün</a></p>

## atheros-compliance-kit'in çalışma zamanı bağımlılığı var mı?

<p class="lead">Sıfatsız dört sayı — her biri build zamanında üründen ölçülüyor, elle yazılmıyor.</p>

:::<div class="grid">
:::<div class="card"><div class="stat good">{{runtime_dependencies}}</div><p class="muted">çekirdekte çalışma zamanı bağımlılığı. Kısıtlı bir CI imajına kurulur.</p></div>
:::<div class="card"><div class="stat good">0</div><p class="muted">bayt veriniz süreçten çıkar. Yükleyecek bir yer yok.</p></div>
:::<div class="card"><div class="stat">{{vendor_criteria}}</div><p class="muted">ağırlıklı satıcı ölçütü; <code>unknown</code> atlanmaz, cezalandırılır.</p></div>
:::<div class="card"><div class="stat">{{tests}}</div><p class="muted">test; ağ yok, API anahtarı yok, bir saniyenin altında.</p></div>
:::</div>

## Hangi EU AI Act yükümlülükleri otomatik olarak kanıtlanabilir?

<p class="lead">Üç boşluk ve her birini kapatan modül.</p>

**Kanıt boşluğu.** Art. 11 ve Annex IV teknik dokümantasyon ister; ISO/IEC 42001 §9.1 izleme kayıtları ister. İkisi de yalnızca çalışan sistemin üretebileceği çıktıları tarif eder — ve ikisi de genellikle bir insanın aylar sonra hafızadan yazdığı bir belgeyle üretilir. `euact` yapıyı üretir ve diğer modüllerin kanıtlayabildiğini doldurur.

**Kara kutu boşluğu.** Bir istem OpenAI, Anthropic ya da Mistral'a gittiği anda, sorumlu olduğunuz veriyi dışa aktarmış ve hakkında güvence veremeyeceğiniz bir çıktıyı içe almış olursunuz. Maskeleme, filtreleme, kayıt ve yedeğe düşme için varsayılan bir yer yoktur. `guard` o yerdir.

**Bilinmeyen bilinmeyenler boşluğu.** RAG külliyatları kayar, gömmeler çarpılır ve önyargı modelden değil bilgi tabanından girer. Herkes modeli denetler. Külliyatı kimse ölçmez. `rag` külliyatı ölçer.

## Her modül ne yapıyor ve hangi maddeyi kanıtlıyor?

<p class="lead">Dört modül, tek bağımlılık.</p>

| | Modül | Yanıtladığı soru |
|---|---|---|
| M1 | `atheros_kit.rag` | Bilgi tabanımız önyargılı, yinelenmiş, kaymış ya da kişisel veri dolu mu? |
| M2 | `atheros_kit.guard` | Üçüncü taraf bir LLM'e ne gidiyor, geriye ne geliyor? |
| M3 | `atheros_kit.euact` | EU AI Act seviyemiz, savunulabilir biçimde nedir — ve Annex IV'te daha ne eksik? |
| M4 | `atheros_kit.vendor` | **Üçüncü taraf / satıcı riski** — bu tedarikçi kullanılabilir mi ve eğitimden çıkma gerçekten uygulanıyor mu? |
| | `atheros_kit.cicd` | Yukarıdakilerden biri gerilediğinde derlemeyi başarısız kıl. |

Her modül kanıtladığı yükümlülüğü adlandırır; böylece hukuki bir görev, bir mühendisin çalıştırabileceği bir komuta eşlenir. Bunların dört ayrı ürün değil tek bir ürün olmasının nedeni bu eşlemedir.

:::<p><a class="cta ghost" href="modules.html">Modül referansını okuyun</a></p>

## EU AI Act kanıtı için kütüphane mi, SaaS mı?

<p class="lead">Neden bu, neden bir yönetişim platformu değil.</p>

**Verinin olduğu yerde çalışır.** Kendi sürecinizde bir kütüphane. Varsayılan olarak veri dışarı çıkmaz, yüklenecek bir şey yoktur, yeniden girilecek bir şey yoktur. Barındırılan bir platform bunu yapısal olarak sunamaz.

**Kurgusu gereği kurcalanma-kanıtlı.** Her değerlendirme, engelleme ve maskeleme, bağımsız bir `verify` komutu olan SHA-256 zincir özetli bir deftere düşer — ve zincirin tamamını tarayıcınızda yeniden hesaplayan ikinci, bağımsız bir doğrulayıcı vardır.

**Düşer, durmaz.** Çekirdek yalnızca standart kütüphanedir. Her yeteneğin anahtarsız ve ağsız çalışan deterministik bir yolu vardır ve yedeğe düşen her çalışma, yedeği gerçekmiş gibi sunmak yerine `degraded` olarak işaretlenir.

## Bir kontrol ölçülemediğinde Kit ne yapıyor?

<p class="lead">Kimsenin göndermediği kısım.</p>

Rakiplerin tüm gösterge panelleri yeşildir. Bizimki neyi tespit edemediğini söyler.

| | |
|---|---|
| Ölçümü olmayan bir skor | `ölçülmedi` olarak görünür ve **kapıyı başarısız kılar** |
| "Hiçbir gösterge eşleşmedi" | asla "düşük risk" olarak gösterilmez |
| Belirsiz bir sınıflandırma | kendinden emin yanlış bir seviye değil, çelişkiyi adlandıran bir **gri bölge** bildirir |
| Bir Annex IV bölümündeki makine kanıtı | onu **kısmi** yapar, asla karşılanmış değil |
| Yanıtsız bir satıcı sorusu | atlanmaz, **cezalandırılır** |
| Hiçbir şey bulamayan yapısal bir dedektör | tanınabilir hiçbir şey bulunmadığı anlamına gelir, hiçbir şey olmadığı değil |

> Ölçüm bozulduğunda yeşile dönen bir kapı, hiç kapı olmamasından kötüdür. Ürün bu cümledir.

:::<p><a class="cta" href="honesty.html">Dürüstlük sözleşmesinin tamamı</a></p>

## Uyum gerilemesinde CI derlemesini nasıl başarısız kılarım?

<p class="lead">Derlemenizi başarısız kılar.</p>

```yaml
# atheros.yml
fail_on:
  fairness_score_below: 70
  quality_score_below: 70
  drift_verdict_in: [shifted]
  risk_tier_in: [unacceptable]
  residency_verdict_in: [non_compliant]
  chain_violation: true
```

```
uyum kapısı — BAŞARISIZ
  ⨯ fairness_score      başarısız  0.0    0.0 < 70
  ⨯ quality_score       başarısız  24.5   24.5 < 70
  ✓ corpus_drift        geçti      stable
  ✓ eu_ai_act_tier      geçti      high
  – vendor              atlandı    modül yapılandırılmamış
  ✓ audit_chain         geçti      sağlam
```

`atlandı` satırına dikkat edin. Neyi kontrol etmediğini gizleyen bir kapı, tam kapsam gibi okunur.

## Satıcı bu aracı kendi ürünü üzerinde çalıştırıyor mu?

<p class="lead">Kendi üzerimizde çalıştırıyor ve sonucu yayımlıyoruz.</p>

Kendi ürünümüzü kendi aracımızla değerlendirip sonucu yayımlıyoruz — %33 Annex IV tamlık skoru ve bilerek kırmızı bırakılmış bir kontrol dâhil. Satıcısı kendi değerlendirmesini üretemeyen bir uyum aracı, kimsenin satın almaması gereken bir araçtır.

Bunu yapmak, kendi yerleşim mantığımızda gerçek bir hata buldu; değişiklik günlüğünde kendi başlığı altında duruyor.

Okuyun: [kendi uyum raporumuz](self-assessment.html) — her CI derlemesinde yeniden üretilip bayatlık kontrolünden geçiyor, yani sayfa artık var olmayan bir sürümü sessizce tarif edemez.

## AtherosAI Compliance Kit neyi yapmaz?

<p class="lead">Sınırlar, açıkça.</p>

- Hukuki tavsiye vermek, belgelendirmek ya da uygunluk değerlendirmesi yapmak.
- Herhangi bir şeyi eğitmek, ince ayarlamak ya da önyargıdan arındırmak. İyileştirme önerir; onu bir insan çalıştırır.
- Külliyatınızı, istemlerinizi ya da satıcı sözleşmelerinizi değiştirmek.
- Verinizi bir yerde saklamak. Raporlar sizin sahip olduğunuz dosyalardır.
- Mevzuat metnini kendi kendine güncellemek. Hukuki içerik sürümlerle gelen sürümlenmiş veridir ve her değerlendirme hangi sürümle çalıştığını kaydeder.

## Hiçbir şey kurmadan gerçek bir raporu görebilir miyim?

<p class="lead">Ne ürettiğini görün.</p>

[Canlı konsol](../demo/), gerçek bir raporu gösteriyor — dört modülün sentetik bir işe alım külliyatı üzerinde çalıştırılmasıyla üretildi; kapı kırmızı, Adillik Skoru ölçülemedi, Annex IV dosyası %33 tam. Her ekran JSON, Markdown veya PDF olarak dışa aktarılıyor ve dışa aktarılan her dosya, örnek olduğunu dosyanın içinde söylüyor.

Statik bir sayfa. Sunucusu, veritabanı ve hiçbir yazma yolu yok — o sayfanın kendi içerik güvenlik politikası, herhangi bir yere bağlanmasını yasaklıyor.

## Nasıl kurarım ve ilk raporu nasıl alırım?

<p class="lead">Buradan başlayın.</p>

```
pip install atheros-compliance-kit          # çekirdek, yalnızca standart kütüphane
pip install 'atheros-compliance-kit[all]'   # bağlayıcılar, PDF dışa aktarım, anlatı katmanı
```

Ücretsiz katman — koruma sarmalayıcısı, risk sınıflandırması ve defterin tamamı — aktivasyon, anahtar ya da ağ gerektirmez. Süresi dolmaz.

:::<p><a class="cta" href="quickstart.html">Hızlı başlangıç</a><a class="cta ghost" href="pricing.html">Fiyatlandırma</a></p>
