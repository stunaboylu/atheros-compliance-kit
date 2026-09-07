# Bu aracın size söylemediği şeyler
> Kit'in ürettiği her skorun neyi tespit ettiği ve neyi tespit etmediği. Her yerden bağlantı verdiğimiz sayfa.

# Bu aracın size söylemediği şeyler

Çoğu uyum aracı, güven verici bir sayı üretmek için optimize edilmiştir. Bu sayfa, bunun bir özellik değil bir başarısızlık biçimi olduğu için var — ve "bunu ölçtük, iyiydi" ile "bunu ölçemedik" arasındaki farkı göremeyen bir müşteriye, daha güzel bir yazı tipiyle sahte güvence satılmış olacağı için.

Aşağıdaki her şey kodda uygulanır ve bir testle korunur. Hiçbiri çıktıya eklenen bir sorumluluk reddi değildir; hepsi çıktının *içindedir*.

## Sözleşme

**1. `None` skoru ölçülmemiştir. Gri görünür, kapıyı başarısız kılar ve asla geçer sayılmaz.**
Eksik bir ölçümü geçer gibi gösteren bir araç bozuk bir ölçüm aletidir. `Score.passed`, `False` yerine `None` döndürür; böylece `if not score.passed` yazan bir çağıran, "kontrol edemedik"i sessizce "başarısız oldu"ya — ya da daha kötüsü, tersine — çeviremez.

**2. "Hiçbir gösterge eşleşmedi" asla "düşük risk" değildir.**
`minimal` sınıflandırma, `evidence_basis: no_indicator_matched` ve bunu açıkça söyleyen bir sınır taşır. Sözlük yapısaldır; kendisine öğretileni tanır, başka bir şeyi değil.

**3. Tespit yokluğu, tanınabilir hiçbir şey bulunmadığı anlamına gelir.**
Bir e-posta adresinin biçimi vardır. Bir kişinin adının yoktur. Kit'in bildirdiği her kişisel veri sayısı bir **alt sınırdır**, asla toplam değil — ve rapor bunu dipnotta değil, sayının göründüğü yerde söyler.

**4. Belirsizlik, kendinden emin bir yanıt değil, bir gri bölge üretir.**
İki Annex III kategorisi, sektör-kullanım senaryosu çelişkisi ya da GPAI artı yüksek riskli konuşlandırma, güveni düşürür, `grey_zone` işaretler ve çelişkiyi adlandırır. Yanlış ve kendinden emin bir seviye, dürüst bir "buna bir insan karar verir"den kötüdür, çünkü kimse onu yeniden incelemez.

**5. Makine kanıtı bir Annex IV bölümünü kısmi yapar, asla karşılanmış değil.**
Annex IV sistemin bir anlatımını ister. Kanıt bunu destekler; yerine geçmez. Dokuz bölümün hepsi için inandırıcı metin üreten bir üretici, tam görünen ama tam olmayan bir belge çıkarır — iç incelemeden geçer, dış incelemede, başarısızlığın pahalı olduğu noktada düşer.

**6. Yedeğe düşme asla sessiz değildir.**
Sağlayıcı hatası, ret, engellenmiş çıktı, tükenmiş bütçe: her düşürülmüş yanıt tetikleyicisini taşır ve ürettiği skor `deterministic · degraded` olarak etiketlenir. Bir uyum ürününde sessiz ve düşük kaliteli bir yedek, kesintiden kötüdür — çünkü kesinti görünür.

**7. Bir satıcı ölçütünde `unknown` atlanmaz, cezalandırılır.**
Yanıtsız bir soru %20 puan alır — tam puan da değil, sıfır da değil. Yalnızca satıcının gönüllü verdiğini puanlamak belirsizliği ödüllendirir: hiçbir şey yanıtlamayan tedarikçi, aksi hâlde her şeyi olumlu yanıtlayanla aynı puanı alırdı.

**8. Defter sınıfları ve sayıları kaydeder, asla değerleri.**
Tespit ettiği kişisel veriyi saklayan bir uyum kaydı, tam da önlemek için var olduğu başarısızlıktır. Bu, çağıranlara bırakılmak yerine `Report.to_dict()` içinde uygulanır — çünkü "çağıran maskelemeliydi" bir kontrol değildir.

**9. Her rapor neyi tespit edemediğini adlandırır.**
`limits[]`, bulgular kadar belirgin biçimde, her iki dilde gösterilir. Ölçülmeyen, ölçülen kadar önemlidir.

**10. Kit değerlendirir ve kanıtlar. Belgelendirme yapmaz.**
Üründe değil, dokümantasyonda değil, bu web sitesinde değil. Bir lint, üretilen hiçbir çıktının ve hiçbir pazarlama sayfasının — İngilizce ya da Türkçe — yasaklı ifadeleri içermediğini doğrular. CI'da çalışır. İyi niyet bir kontrol değildir.

**11. Bir çerçeve, numarasıyla değil kapsanan maddeleriyle anılır.**
"ISO/IEC 42001 uyumluluğu" demek, aynı sahte güvencenin başka bir tonda söylenmesi olurdu. Araç adı konmuş {{iso_clause_count}} madde için kayıt üretir, başkası için üretmez — [SSS bunları listeler](faq.html) ve `atheros-kit iso export` ile yazılan her kanıt paketi, kapsanmayanların listesini de taşır; böylece belge bizden çıktıktan sonra olduğundan geniş okunamaz. 4–7. ve 10. maddeler, 9.2 iç denetim programı, 9.3 yönetim gözden geçirmesi, Uygulanabilirlik Bildirimi ve Ek A kontrolleri yönetim sistemi işidir; bir CI hattının içindeki hiçbir araç bunları yapmaz. Bir madde, 6.1.2, bizim tarafımızdan karşılanmaz, yalnızca beslenir ve geçtiği her yerde böyle etiketlenir. Aynısı Yönetmelik için de geçerlidir: araç yükümlülükleri kanıtlar, uygunluğu belirlemez ve onaylanmış kuruluş değildir.

## Sayılar nereden gelir ve nerede durur

### Adillik Skoru
Değerlendirilebilen boyutlar üzerinden harmonik ortalama. Harmonik, çünkü çöken bir boyut dört iyi boyut tarafından ortalamayla yok edilmemeli — coğrafyada iyi, cinsiyette felaket olan bir külliyat "çoğunlukla adil" değildir.

**Şurada durur:** önce İngilizce sözlükler, yapısal eşleme ve insanlar yerine yüzey terimleri. `assessed_dimensions` ve `unassessable` konsola kadar ayrı alanlardır ve hiçbir şeyin ölçülemediği bir külliyat 100 değil `None` alır. Sessizlik adillik değildir.

### Anlamsal kayma
Ağırlık merkezi kayması artı boyut bazlı PSI — çoğu uygulamanın atladığı iki düzeltmeyle:

- **PSI'nın örneklem büyüklüğüne bağlı bir gürültü tabanı vardır.** 10 kovayla 200 parçada, iki *özdeş* külliyat yaklaşık 0,09 ortalama PSI alır — yayımlanmış 0,10 "kararlı" bandından ayırt edilemez. Bantlar, gerçek örneklem büyüklüğü için tabanı aşacak biçimde yükseltilir ve düzeltme sınırlarda yazılır. Değişmemiş girdide alarm veren bir kayma izleyicisi susturulur ve susturulmuş bir izleyici hiç olmamasından kötüdür.
- **Sıfıra yakın bir ağırlık merkezinin yönü anlamsızdır.** Gömmeler izotropiğe yakınken iki ağırlık merkezi arasındaki açı gürültüdür: *aynı* dağılımdan iki örnek sıfıra yakın kosinüs alır ve "kaymış" okunur. Sinyal yönlülük açısından ölçülür, hiçbir bilgi taşımadığında dışlanır ve dışlama belirtilir.

**Şurada durur:** geometri. Bir külliyat vektörlerin yakalamadığı biçimlerde anlamsal olarak kayabilir ve `stable` kararı içerik kalitesi hakkında bir ifade değildir.

### EU AI Act sınıflandırması
Kanuni sıra — Art. 5 yasağı, sonra yüksek risk için Annex I ve Annex III, sonra Art. 50, sonra asgari — **sürümlenmiş** bir sözlüğe karşı. Her sınıflandırma `regulation_version` kaydeder; böylece uyuşmayan iki değerlendirme açıklanabilir.

**Şurada durur:** sizin yazdığınız bir açıklamayı okuyan bir kural motoru olmakta. Hukuki görüş değildir, Art. 5'in dar istisnalarının hiçbirini değerlendirmez ve Art. 2 ülkesel kapsamı belirlemez.

### Satıcı skoru
Altı grupta 24 ağırlıklı ölçüt. Ağırlıklar, doğrulaması kolay olanı değil, müşteriyi gerçekten koruyanı kodlar: imzalı bir veri işleme sözleşmesi ve uygulanabilir SCC'ler, bir durum sayfasından bir büyüklük mertebesi ağır basar.

**Şurada durur:** ona söylediğinizde. Başlangıç satıcı bilgileri tarihlidir ve 180 gün sonra eskir — araç kendi verisini kendi raporlarında eski olarak işaretler. Bunlar neyin doğrulanacağına dair bir hatırlatmadır, doğrulamanın yerine geçmez.

## Denetim zinciri

Her modül, sahibi olduğunuz SHA-256 zincir özetli bir JSONL deftere ekleme yapar. `atheros-kit audit verify` her özeti yeniden hesaplar; konsol onları tarayıcınızda yeniden, bağımsız olarak hesaplar — yazanla kodu paylaşan bir doğrulayıcı yalnızca birbirleriyle anlaştıklarını kanıtlayabilir.

**`sağlam` ne demektir:** silme, yeniden sıralama ve düzenleme tespit edilebilir.

**Ne demek değildir:** içeriğin doğru olduğu. Zincir neyin kaydedildiğine tanıklık eder, kaydın arkasındaki değerlendirmenin doğru olup olmadığına değil.

## Kendi raporumuz

Kit'i her sürümde Kit üzerinde çalıştırıyoruz ve bu çalışma bir sürüm kapısıdır. `minimal` seviye, %33 Annex IV tamlığı ve geçene kadar eşik yükseltmek yerine kırmızı bıraktığımız bir kontrol bildiriyor — kapı yeşile dönene kadar ayarlanmış bir eşik, hiçbir şey ölçmeyen bir eşiktir.

Bunu yapmak yerleşim mantığımızda gerçek bir hata buldu: Standart Sözleşme Maddeleri beyan eden sağlayıcılar için `non_compliant` bildiriyordu — oysa SCC, yeterlilik kararı olmayan ülkeler için tam da o mekanizmadır. Bulgu kendi ifadesiyle çelişiyordu. Düzeltildi, testi var ve değişiklik günlüğünde kendimizde bulduğumuz kusurlar başlığı altında duruyor.
