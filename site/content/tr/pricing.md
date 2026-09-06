# Fiyatlandırma
> Kullanım değil, koltuk ve hak. Size hizmet etmenin marjinal maliyeti fiilen sıfır olduğu için çalışmalarınızı ölçmek rant olurdu.

# Fiyatlandırma

**Kullanımı ölçmüyoruz.** Kütüphane sizin sürecinizde, sizin işlem gücünüzde, sizin model anahtarınızla çalışır. Çıkarım barındırmıyor, rapor almıyor ve müşteri verisi saklamıyoruz; dolayısıyla yansıtacağımız bir çalışma başına maliyet yok — ve bunu ölçmek, teknik bir alıcının anında tanıyacağı bir rant olurdu.

Ayrıca tam da istediğimiz davranışı cezalandırırdı: kapıyı her commit'te çalıştırmak.

## Katmanlar

| | Ücretsiz | Takım | Kurumsal |
|---|---|---|---|
| Fiyat | €0 | geliştirici başına €79 / ay, en az 5 koltuk | €1.150 / ay'dan başlar |
| Yıllık | — | geliştirici başına €790 / yıl | teklife bağlı |
| Modüller | `guard` + `euact` classify | dördü de | dördü de |
| CI kapısı | – | var | var |
| Annex IV dosya dışa aktarımı | – | Markdown, JSON | + PDF, özel şablon |
| Vektör bağlayıcıları | bellek içi | dördü de | + desteklenen bir özel bağlayıcı |
| Satıcı kaydı | 3 sağlayıcı | tümü | + kendi tedarikçileriniz, bizim bakımımızla |
| Denetim zinciri | **tam** | tam | + imzalı sürüm doğrulaması |
| Destek | GitHub issue | 2 iş günü | 4 iş saati, ortak kanal, atanmış mühendis |
| Hava boşluklu paket + SBOM | – | – | var |
| Güvenlik anketi desteği | – | – | var |
| Mevzuat sürümü SLA'sı | en iyi çaba | 60 gün içinde | 30 gün içinde, yazılı etki notuyla |

## Ücretsiz katman neden defterin tamamını içerir

Kurcalanma kanıtını kilitlemek kolay olurdu. Aynı zamanda bir hata olurdu: zincir, ücretsiz katmanın çıktısını bir oyuncak değil *kanıt* yapan şeydir ve bir mühendisin onu bir meslektaşına göstermesinin nedenidir. Kilitlemek, bunların işe yaramasının nedenini ortadan kaldırırdı.

Ücretsiz katmanın süresi dolmaz, aktivasyon gerektirmez ve herhangi bir sayıda kişi tarafından ticari olarak kullanılabilir.

## Kurumsal aslında ne içindir

Daha fazla özellik için değil. 90 soruluk bir yapay zekâ güvenlik anketiyle tıkanmış kurumsal bir anlaşması olan müşteri içindir — onun için Kit bir anlaşma sigortasıdır ve bu katman anket yanıtını, müzakere edilmiş veri işleme sözleşmesini, hava boşluklu paketi ve atanmış bir mühendisi satın alır.

## Bizim taşıdığımız maliyet

Mevzuat bakımı. EU AI Act'in uygulama tasarrufları, uyumlaştırılmış standartları ve Annex III yorumları yıllarca hareket edecek ve her hareket, nitelikli birinin gözden geçirdiği sürümlenmiş bir sözlük güncellemesidir. Bunu saf yazılım gibi fiyatlayan bir rakip yeterince yatırım yapmayacak ve yanıtları sessizce çürüyecektir.

Kurumsal katmanın açık bir mevzuat sürümü SLA'sı taşımasının nedeni budur: SLA, bakımı finanse edilebilir kılan şeydir ve eskimiş bir hukuki sözlük, hiç araç olmamasından kötüdür.

## Sorular

`sales@atheros.ai`

