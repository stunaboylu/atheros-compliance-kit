# Sıkça sorulan sorular
> Veri süreçten çıkıyor mu, bu bir belgelendirme mi, "ölçülmedi" ne demek, hangi modül hangi maddeyi kanıtlıyor ve maliyeti nedir.

# Sıkça sorulan sorular

### Bu aracı kullanınca verim sürecimden çıkıyor mu?

Hayır. {{modules}} modülün tamamı sizin sürecinizde, sizin işlem gücünüzde bir kütüphane olarak
çalışır. Veri alan bir uç nokta yok, varsayılan açık telemetri yok, lisans nabzı yok — lisans
token'ı, pakete gömülü bir anahtara karşı 90 gün boyunca çevrimdışı doğrulanır. Aracın
yapabileceği tek dış çağrı, `GuardedClient` üzerinden, sizin anahtarınızla, sizin sağlayıcınıza
yapılan kendi model çağrılarınızdır — onlar da isteğe bağlıdır, çünkü her modülün anahtarsız ve
ağsız çalışan deterministik bir yolu vardır. Çekirdek {{runtime_dependencies}} üçüncü taraf paket
alır ve bir CI işi bunu her commit'te doğrular.

### Bu bir belgelendirme mi, bizi uyumlu kılıyor mu?

İkisi de değil. AtherosAI Compliance Kit **değerlendirme ve kanıt** üretir — değerlendirir ve
kanıtlar, belgelendirme yapmaz. (AB) 2024/1689 sayılı Tüzük anlamında bir uygunluk değerlendirmesi
değildir ve hukuki tavsiye değildir. Mevzuat
yükümlülükleri sizde kalır ve bu aracın hiçbir çıktısı onları devretmez. Üretilen her raporu ve
her pazarlama sayfasını — İngilizce ve Türkçe — tarayan bir lint, "belgelendirilmiş", "tamamen
uyumlu", "uyum garantisi" ya da "ek işlem gerekmez" ifadeleri geçerse build'i kırar.

### "Ölçülmedi" ne demek ve neden build'imi kırıyor?

`ölçülmedi` skoru, ölçümün çalışmadığı ya da hesaplanamadığı anlamına gelir — geçtiği değil. Gri
görünür, asla yeşil değil, ve CI kapısını başarısız kılar. Geçer saymak, kapının tam da olmaması
gereken anda yeşile dönmesi demektir: ölçümün kendisi bozulduğunda. Ürünün üzerine kurulu olduğu
tek tasarım kararı budur ve dokümandaki bir niyet olarak değil kodda uygulanır.

### Hangi modül hangi EU AI Act maddesini kanıtlıyor?

Her yükümlülük, kanıtını üreten modülü adlandırır.

| Madde | Yükümlülük | Kanıtı üreten |
|---|---|---|
| Art. 9 | Risk yönetim sistemi | `euact.dossier` |
| Art. 10 | Veri yönetişimi ve önyargı incelemesi | `rag.bias` + `rag.quality` |
| Art. 11 + Annex IV | Teknik dokümantasyon | `euact.dossier` |
| Art. 12 | Otomatik olay kaydı | `core.audit` + `guard.ledger` |
| Art. 13 | Şeffaflık ve kullanım talimatları | `euact.dossier` |
| Art. 14 | İnsan gözetimi | `guard.fallback` |
| Art. 15 | Doğruluk, sağlamlık, siber güvenlik | `guard.injection` |
| Art. 17 | Kalite yönetim sistemi | `cicd.gate` |
| Art. 26 | Dağıtıcı yükümlülükleri | `guard.ledger` |
| Art. 50 | Üretken sistemler için şeffaflık | `euact.transparency` |
| ISO/IEC 42001 §9.1 | İzleme kayıtları | `core.audit` |

### Bu, ISO/IEC 42001'in hangi maddelerini kapsıyor?

{{iso_clause_count}} madde, ve araç hangileri olduğunu açıkça söylüyor. Adı konmuş maddeler **için kanıt üretir** — standardın iç denetimini otomatikleştirmez ve buradaki hiçbir şey standardı uçtan uca kapsıyormuş gibi okunmamalıdır.

{{iso_clause_table}}

6.1.2 maddesi, karşılanan değil beslenen bir madde olarak listelenir. EU AI Act risk sınıflandırması düzenleyici bir kategorilendirmedir; madde ise sizin kendi yapay zekâ risk ölçütlerinizi, analizinizi ve değerlendirmenizi ister. `atheros-kit iso export` bu ayrımı maddenin kendi altına yazar, ki denetçiye hiçbir zaman işine gelen okuma sunulmasın.

**Kapsanmayan:**

{{iso_not_covered}}

Bunlar, CI'nızın içinde çalışan bir aracın sizin yerinize yapamayacağı yönetim sistemi işleridir; aksini ima eden bir rapor, bu ürünün önlemek için var olduğu başarısızlık olurdu.

### API anahtarı ve internet bağlantısı olmadan çalışır mı?

Evet, ve bu düşürülmüş bir mod değil, desteklenen varsayılandır. Her modülün deterministik bir
yolu vardır. `atheros-kit doctor`, hangi sağlayıcılar için anahtar tuttuğunuzu ve dolayısıyla her
kontrolün hangi yolu izleyeceğini yazdırır. Bir model yapılandırılmış ama yanıt vermemişse skor
`degraded` etiketlenir ve rapor bunu söyler — yedeğe düşme asla sessiz değildir.

### Bu bir kütüphane mi, yoksa bir yönetişim platformu mu?

Bir kütüphane ve bir CLI; artı kütüphanenin ürettiği raporları gösteren salt okunur bir konsol.
Verinin olduğu yerde çalışır. Barındırılan bir platform bu iddiayı yapısal olarak edemez —
konsolun sunucusu, veritabanı ve hiçbir yazma yolu olmamasının, ve planlanmış bir SaaS sürümü
bulunmamasının nedeni budur.

### Maliyeti nedir ve nasıl ölçülür?

Ölçülmez. Araç sizin işlem gücünüzde, sizin model anahtarınızla çalışır; yansıtılacak bir çalışma
başına maliyet yoktur — ve ölçmek, ürünün istediği davranışı, yani kapıyı her commit'te
çalıştırmayı cezalandırırdı.

| Katman | Fiyat | İçerik |
|---|---|---|
| Ücretsiz | €0, aktivasyon yok, süresiz | Korumalar, risk sınıflandırması, defterin tamamı |
| Takım | geliştirici başına €79/ay, en az 5 koltuk | Dört modül, CI kapısı, dosya dışa aktarımı |
| Kurumsal | €1.150/ay'dan | Hava boşluklu paket, SBOM, güvenlik anketi desteği, 30 günlük mevzuat SLA'sı |

### Hangi vektör veritabanları destekleniyor?

{{vector_stores}} bağlayıcı gelir: Chroma, pgvector, Pinecone ve Milvus. Başka bir şey için
külliyatı kendiniz okuyup parçaları verirsiniz — bu yol yedek değil birinci sınıf bir yoldur ve
değerlendirme kodunun hiçbir sürücüye dokunmamasının nedeni budur. Her bağlantı kurgusu gereği
salt okunurdur; iyileştirme, bir insanın çalıştıracağı tarifler üretir ve külliyatınızı asla
değiştirmez.

### Bir denetçi denetim zincirini bağımsız olarak nasıl doğrular?

İki bağımsız uygulama. `atheros-kit audit verify` her SHA-256 özetini Python'da yeniden hesaplar;
konsol, zincirin tamamını tarayıcıda WebCrypto ile, yazanla hiçbir kod paylaşmadan yeniden
hesaplar — yazanla kodu paylaşan bir doğrulayıcı yalnızca birbirleriyle anlaştıklarını
kanıtlayabilir. Sağlam bir zincir silmeyi, yeniden sıralamayı ve düzenlemeyi tespit edilebilir
kılar. İçeriği doğru kılmaz: zincir neyin kaydedildiğine tanıklık eder, kaydın arkasındaki
değerlendirmenin doğru olup olmadığına değil.

### Ücretsiz katmanın süresi doluyor mu?

Hayır. Aktivasyon, anahtar ve ağ çağrısı gerektirmez, herhangi bir sayıda kişi tarafından ticari
olarak kullanılabilir ve süresi dolmaz. Koruma sarmalayıcısını, EU AI Act risk sınıflandırmasını
ve zincir özetli defterin tamamını kapsar. Defteri kilitlemek kolay olurdu ve ücretsiz katmanı bir
oyuncak değil kanıt yapan şeyi ortadan kaldırırdı.

### Sistemimin EU AI Act kapsamında yüksek riskli olup olmadığını nasıl anlarım?

Sektörünüz ve kullanım senaryolarınızla `atheros-kit euact classify` çalıştırın. Motor kanuni
sırayla değerlendirir — önce Art. 5 yasakları, sonra Annex I ürün güvenliği ve
{{annex_iii_categories}} Annex III kategorisi, sonra Art. 50 şeffaflık, sonra asgari — sürümlenmiş
bir sözlüğe karşı ({{regulation_version}}), ve her sınıflandırma hangi sürümle çalıştığını
kaydeder. Girdiler birden fazla yanıtı destekliyorsa kendinden emin bir seviye yerine çelişkiyi
adlandıran bir **gri bölge** bildirir; `minimal` kararı ise hiçbir göstergenin eşleşmemesine
dayandığını, bunun da düşük risk kanıtı olmadığını açıkça söyler.

### Annex IV dosyasının ne kadarı otomatik doldurulabilir?

Bir kısmı, ve rapor hangi kısım olduğunu söyler. Üretici {{annex_iv_sections}} bölümün tamamını
oluşturur ve her birini `karşılandı`, `kısmi` ya da `eksik` olarak işaretler. Makine kanıtı bir
bölümü **kısmi** yapar, asla karşılanmış değil: Annex IV sistemin bir anlatımını ister, kanıt bunu
destekler ama yerine geçmez. Kendi öz-değerlendirmemiz kendi ürünümüz için %33 tamlık skorunu
eksik hâliyle yayımlar — çünkü dokuz bölümün hepsi için inandırıcı metin üreten bir üretici, tam
görünen ama tam olmayan, iç incelemeden geçip dış incelemede düşen bir belge çıkarır.
