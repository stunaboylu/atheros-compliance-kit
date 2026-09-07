# Fiyatlandırma
> Aktivasyonsuz ve süresiz €0 ücretsiz katman, takımlar için geliştirici başına aylık €79, kurumsal için aylık €1.150'den başlayan fiyat. Koltuk ve hak — asla kullanım ölçümü.

:::<p class="eyebrow">Koltuk, sayaç değil</p>

# AtherosAI Compliance Kit'in maliyeti nedir?

<p class="lead">Üç katman. Ücretsiz olan aktivasyon, anahtar ve ağ çağrısı gerektirmez, ve süresi dolmaz.</p>

:::<div class="tiers">
:::<div class="tier"><h3>Ücretsiz</h3><p class="who">Değerlendirenler, ya da henüz bir uyum programı olmadan korumaları üretimde çalıştıranlar.</p><div class="price"><span class="amount">€0</span></div><p class="sub">Aktivasyon yok. Süre yok. Ticari kullanım serbest.</p><ul><li><code>guard</code> — kişisel veri maskeleme ve {{injection_signatures}} imzalı enjeksiyon güvenlik duvarı</li><li><code>euact</code> risk sınıflandırması, {{annex_iii_categories}} Annex III kategorisinin tamamı</li><li>Zincir özetli defterin <strong>tamamı</strong></li><li>İngilizce ve Türkçe</li><li class="no">CI kapısı</li><li class="no">Annex IV dosya dışa aktarımı</li><li class="no">Külliyat denetimi ve üçüncü taraf satıcı değerlendirmesi</li></ul><a class="cta" href="quickstart.html">Beş dakikada başlayın</a></div>
:::<div class="tier featured"><span class="flag">Çoğu takım</span><h3>Takım</h3><p class="who">Yaptığını kanıtlaması istenen bir mühendislik takımı — genellikle ilk kurumsal anketten sonra.</p><div class="price"><span class="amount">€79</span><span class="unit">/ geliştirici / ay</span></div><p class="sub">En az 5 koltuk · geliştirici başına €790 / yıl (iki ay bedava)</p><ul><li>Ücretsiz katmandaki her şey</li><li><strong>Dört modülün tamamı</strong> — külliyat önyargısı ve kalitesi, korumalar, sınıflandırma, üçüncü taraf satıcı riski</li><li>GitHub Actions ve GitLab şablonlarıyla CI kapısı</li><li>Annex IV dosya dışa aktarımı (Markdown, JSON)</li><li>{{vector_stores}} vektör veritabanı bağlayıcısının tamamı</li><li>Özel önyargı boyutları ve özel varlık maskeleme</li><li>E-posta desteği, 2 iş günü</li></ul><a class="cta" href="mailto:sales@atheros.ai?subject=Takim%20katmani">Bizimle konuşun</a></div>
:::<div class="tier"><h3>Kurumsal</h3><p class="who">Güvenlik anketiyle tıkanmış bir anlaşma, ya da hava boşluklu bir ağda çalışması gereken bir sistem envanteri.</p><div class="price"><span class="amount">€1.150</span><span class="unit">/ ay ve üzeri</span></div><p class="sub">Yıllık, teklife bağlı. Tipik olarak yılda €13,8k–34k.</p><ul><li>Takım katmanındaki her şey</li><li><strong>Güvenlik anketi desteği</strong> — bu katmanın alınma sebebi genellikle budur</li><li>CycloneDX SBOM ile hava boşluklu paket</li><li>PDF dosya dışa aktarımı ve özel şablonlar</li><li>Kendi tedarikçileriniz satıcı kaydında bizim bakımımızla</li><li>Müzakere edilmiş veri işleme sözleşmesi ve şartlar</li><li><strong>30 günlük mevzuat sürümü SLA'sı</strong>, yazılı etki notuyla</li><li>Atanmış mühendis, ortak kanal, 4 iş saati</li></ul><a class="cta" href="mailto:sales@atheros.ai?subject=Kurumsal">Teklif isteyin</a></div>
:::</div>

## Kullanım neden ölçülmüyor?

Çünkü size hizmet etmenin marjinal maliyeti fiilen sıfır. Kütüphane sizin sürecinizde, sizin işlem gücünüzde, sizin model anahtarınızla çalışır. Çıkarım barındırmıyor, rapor almıyor ve müşteri verisi saklamıyoruz; yansıtılacak bir çalışma başına maliyet yok — ve yine de ücretlendirmek rant olurdu, ki teknik bir alıcı bunu anında tanır.

:::<p class="note">Ayrıca ürünün teşvik etmek için var olduğu davranışı cezalandırırdı: kapıyı her commit'te çalıştırmayı. Sizi daha seyrek kontrol etmeye iten bir fiyat, satın aldığınız şeye karşı çalışan bir fiyattır.</p>

## Ücretsiz katman neden defterin tamamını içeriyor?

Kurcalanma kanıtını kilitlemek kolay olurdu ve bir hata olurdu. Zincir özetli defter, ücretsiz katmanın çıktısını bir gösteri değil *kanıt* yapan şeydir; bir mühendisin onu bir meslektaşına göstermesinin nedeni de odur. Kilitlemek, bunların işe yaramasının sebebini ortadan kaldırırdı.

Ücretsiz katman aktivasyon gerektirmiyor, yani ürünü değerlendirdiğinizi öğrenmiyoruz — öğrenebileceğimiz bir mekanizma yok.

## Kurumsal katman aslında ne için?

Daha fazla özellik için değil. Doksan soruluk bir yapay zekâ güvenlik anketinin arkasında tıkanmış kurumsal bir anlaşması olan takım için. Onlar için Kit bir anlaşma sigortasıdır; katman, anket yanıtını, müzakere edilmiş veri işleme sözleşmesini, hava boşluklu paketi ve atanmış bir mühendisi satın alır — üstelik tıkanan sözleşmenin yanında yuvarlama hatası kalan bir fiyata.

## Kaynak okunabilirken ne için ödüyoruz?

Wheel, {{modules}} okunabilir Python dosyasıdır: paketi kuran herkeste kaynak vardır. Bu, saf Python dağıtımının doğasıdır ve bilinçlidir — çünkü denetçinin inceleyemediği bir uyum aracı, denetçinin kabul edemeyeceği bir araçtır.

Ödediğiniz şey, sürekli yapılması gereken iş:

- **Mevzuat bakımı.** EU AI Act'in uygulama tasarrufları, uyumlaştırılmış standartları ve Annex III yorumları yıllarca hareket edecek. Her hareket, nitelikli birinin gözden geçirdiği sürümlenmiş bir sözlük güncellemesidir. Bunu saf yazılım gibi fiyatlayan bir rakip yeterince yatırım yapmayacak ve yanıtları sessizce çürüyecek.
- **Sayıların arkasındaki taahhüt.** SLA, destek, ve aracı her derlemede kendi ürünümüz üzerinde çalıştırıp [sonucu boşluklarıyla yayımlamamız](self-assessment.html).

## Sorular

`sales@atheros.ai` · Kit değerlendirir ve kanıtlar. Belgelendirme yapmaz.
