# Modüller
> Dört modül, her birinin ne ölçtüğü ve nerede durduğu.

# Modüller

Tek bir çekirdek üzerinde dört modül. Birini ya da hepsini kullanın. `core` onlardan hiçbir şey almaz ve onlar da paylaşılan bir bulgu sözlüğü dışında birbirlerinden hiçbir şey almaz — bir modülün eklerini kurup diğerlerini kurmamanızı sağlayan da budur.

## M1 · `atheros_kit.rag` — külliyat kalitesi ve önyargı

Modeli değil **külliyatı** ölçer. Boşluk budur: ekipler yanıtları değerlendirir ve o yanıtların çekildiği bilgi tabanına hiç bakmaz — oysa bir RAG sisteminde önyargı, ağırlıklardan çok daha sık külliyattan girer.

| Yetenek | Çıktı |
|---|---|
| Bağlayıcılar | bellek içi, Chroma, pgvector, Pinecone, Milvus — kurgusu gereği salt okunur |
| Parça kalitesi | boş, neredeyse boş, birebir ve yakın yinelemeler, gömmesizler, karışık boyutlar, boyut aykırıları, kişisel veri |
| Anlamsal kayma | ağırlık merkezi kayması, boyut bazlı PSI, hacim değişimi — örneklem gürültü tabanı ve izotropi kontrolüyle |
| Önyargı | yedi boyut, temsil (beşte-dört kuralı) ve bağlamsal çerçeveleme → Adillik Skoru |
| İyileştirme | sıralı tarifler; üretilir, asla çalıştırılmaz |

**Nerede durur:** sözlükler önce İngilizce ve yapısaldır. `assessed_dimensions` ile `unassessable` ayrı alanlardır ve hiçbir şeyin ölçülemediği bir külliyat 100 değil `None` alır.

## M2 · `atheros_kit.guard` — üçüncü taraf API korumaları

Uygulamanız ile harici model arasındaki yalıtım katmanı. Sağlayıcıdan bağımsız: bir çağrılabiliri sarar, çünkü her sağlayıcının istemci nesnesi farklıdır ve hepsi değişir — ama `str -> str` değişmez.

| Yetenek | Ayrıntı |
|---|---|
| Kişisel veri ve özel varlıklar | Kararlı yer tutucular (`⟦EMAIL_1⟧`), böylece model iki kişiyi hâlâ ayırt edebilir. Bellekte geri döndürülebilir kasa ya da `reversible=False` ile kurgusu gereği geri döndürülemez. |
| Sağlamalar | Luhn, IBAN mod-97, TCKN, BSN — böylece bir sipariş numarası kimlik numarası olarak kaydedilmez |
| Enjeksiyon güvenlik duvarı | Talimat geçersiz kılma, istem sızdırma, jailbreak kişilikleri, karar manipülasyonu, sınırlayıcı taklidi, araç kaçakçılığı ve çözülüp yeniden taranan **kodlanmış yükler** |
| Token yönetişimi | Bütçeler çağrıdan *önce* uygulanır — sonradan kontrol edilen bir bütçe kontrol değil, rapordur |
| Yedeğe düşme | Yeniden dene → ikincil → statik; her adım kaydedilir, asla sessiz değil |

Üç hazır ayar: `observe()` ölçer, hiçbir şey engellemez; `standard()` maskeler ve kritik imzaları engeller; `strict()` kasayı tamamen bırakır ve şüpheli her şeyde hata fırlatır.

**Nerede durur:** güvenlik duvarı bilerek imza tabanlıdır — istemlenebilen bir sınıflandırıcı bir kontrol değildir. LLM hakem ikinci görüş olarak vardır, asla tek görüş olarak değil. Akış hâlinde araya girme v1'de desteklenmez.

## M3 · `atheros_kit.euact` — sınıflandırma ve Annex IV

| Yetenek | Ayrıntı |
|---|---|
| Sınıflandırma | Kanuni sıra: Art. 5 → Annex I / Annex III → Art. 50 → asgari; sürümlenmiş sözlüğe karşı |
| Gri bölge | Birden çok Annex III eşleşmesi, sektör çelişkileri ya da GPAI artı yüksek risk güveni düşürür ve çelişkiyi adlandırır |
| Yükümlülükler | Her görev, kanıtını üreten modülü taşır — dört modülü tek ürün yapan omurga |
| Dosya | Annex IV bölüm 1–9; her biri `karşılandı` / `kısmi` / `eksik`, boşluklar boşluk olarak yazılır |
| Şeffaflık | Art. 50 sıfır genişlikli işaretleme, doğrulama, C2PA biçimli üstveri |

**Nerede durur:** sizin yazdığınız bir açıklamayı okuyan bir kural motorudur. Art. 5'in dar istisnalarını değerlendirmez ve Art. 2 ülkesel kapsamını belirlemez.

## M4 · `atheros_kit.vendor` — üçüncü taraf ve satıcı riski

| Yetenek | Ayrıntı |
|---|---|
| 24 ölçüt | Sertifikalar, veri koruma, saklama ve eğitim, güvenlik, yapay zekâ şeffaflığı, operasyon — ağırlıklı |
| `unknown` | Atlanmaz, %20 puanla cezalandırılır. Bir satıcı yanıt vermeyerek iyi puan alamaz. |
| Yerleşim | Yeterlilik, SCC, BCR; AB–ABD çerçevesi *alıcının* sertifikasyonunu gerektirir ve bu açıkça kontrol edilir |
| Çıkma | Mevcut ≠ etkin ≠ sözleşmesel — üç olgu, ayrı ayrı bildirilir |
| Kayıt | Tarihli başlangıç satıcı bilgileri; 180 gün sonra eskir ve aracın kendisi bunu işaretler |

**Nerede durur:** başlangıç kaydı, bir satıcının neyi sunduğunu tarif eden kamuya açık dokümantasyondur — hesabınızda neyin yapılandırıldığını ya da sözleşmenizde neyin yazdığını değil. Kendi yanıtlarınızı `overrides=` ile geçirin.

## `atheros_kit.cicd` — kapı

Ölçtüğünüzü yapılandırılmış eşiklerle karşılaştırır, `atheros-report.json` ve bir Markdown özeti yazar, çıkış kodunu belirler. GitHub Actions ve GitLab CI şablonları gelir.

İki kural: **ölçülmemiş bir kontrol asla geçmez** ve **atlanan her kontrol yazılır**. Sessiz kısmi kapsam, tam kapsam gibi okunur.

## `atheros_kit.iso` — ISO/IEC 42001 kanıt paketi

```
atheros-kit iso export --lang tr --out ./kanit
```

Zincir özetli defteri, bir denetçinin okuyabileceği tek bir belgede toplar: kayıtlar kanıtladıkları maddenin altında gruplanmış, zincir doğrulaması, **hiç** kaydı olmayan maddeler ve aracın kapsamadıklarının tam listesi. Hiçbir şey üretmez — her satır, özeti üzerinden bir defter satırına kadar izlenir.

Belgeyi pazarlama değil kanıt yapan üç özellik var. Yalnızca **defterin bir fonksiyonudur**: üretim zaman damgası ya da koşu kimliği yoktur, dolayısıyla belgeden şüphelenen denetçi komutu yeniden çalıştırıp farkı alır. **Kırık zincir kanıtın altında değil üstünde** bildirilir ve komut 1 ile çıkar — bunu susturacak bir bayrak yoktur, çünkü uyarıyı bastıran bir bayrak, uyarının bastırılma yolu hâline gelir. Ve **boş defter başarılı bir dışa aktarım değildir**: hiç kanıt içermeyen bir paketi yeşil çıkış koduyla üreten komut, operatörü tam da önemli olduğu anda yanıltmıştır.

6.1.2 maddesi geçtiği her yerde *yalnızca girdi* olarak etiketlenir. EU AI Act sınıflandırması düzenleyici bir kategorilendirmedir; madde ise sizin kendi risk ölçütlerinizi, analizinizi ve değerlendirmenizi ister. Bkz. [bu araç size neyi söylemez](honesty.html).

## `atheros_kit.core` — temeller

Yalnızca standart kütüphane. Zincir özetli denetim defteri, katmanlı yapılandırma, model kademe soyutlaması, paylaşılan bulgu sözlüğü ve — maskeleme çağıranlara bırakılmayıp serileştirmede uygulanarak — İngilizce ve Türkçe rapor üretimi.
