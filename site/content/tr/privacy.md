# Gizlilik
> Kit'in ne gönderdiği, servislerimizin ne sakladığı ve ikisini de kendiniz nasıl kontrol edeceğiniz.

# Gizlilik

Yapay zekâ sistemlerini yönetmek için bir araç satıyoruz. Yapabileceğimiz en az şey, başkalarının satıcılarına sorduğumuz soruları yanıtlayabilmektir.

## Kit ne gönderir: hiçbir şey

Kütüphane sizin sürecinizde çalışır. Varsayılan olarak açık telemetrisi, lisans nabzı ve raporlama uç noktası yoktur. Bir raporun yüklenebileceği bir yer yoktur, çünkü öyle bir şey işletmiyoruz.

Kit'in yapabileceği tek dış çağrı, `GuardedClient` üzerinden, **sizin anahtarınızla**, **sizin sağlayıcınıza** yapılan **kendi model çağrılarınızdır**. Bunlar da isteğe bağlıdır: her modülün anahtarsız ve ağsız çalışan deterministik bir yolu vardır.

Buna inanmak zorunda değilsiniz:

```
pip install atheros-compliance-kit
python -c "import sys, atheros_kit.core; print([m for m in sys.modules if 'requests' in m or 'http' in m])"
```

Çekirdek hiçbir üçüncü taraf modülü almaz. Bir CI işi bunu her commit'te doğrular, çünkü gelecekteki bir pull request'teki tek bir kolaylık import'u bu sözü sessizce bozardı.

## Ücretsiz katman ne ister: aktivasyon yok

Koruma sarmalayıcısı, risk sınıflandırması ve defterin tamamı lisans anahtarı, token ya da ağ çağrısı olmadan çalışır. Ürünü değerlendirdiğinizi öğrenmeyiz, çünkü öğrenebileceğimiz bir mekanizma yoktur.

## İsteğe bağlı telemetri

Varsayılan olarak kapalı. `ATHEROS_TELEMETRY=1`, çalışma başına bir kez şunu gönderir, başka hiçbir şeyi değil:

```json
{"version": "1.0.0", "python": "3.12", "os": "linux",
 "modules_used": ["guard", "euact"], "checks_run": 7,
 "duration_ms": 4210, "degraded": false, "license_tier": "team"}
```

Skor yok. Bulgu yok. Özne adı yok. Sağlayıcı adı yok. Ölçtüğünüz hiçbir şeyin sayısı yok. Yukarıdaki şema şemanın tamamıdır, bir testle doğrulanır ve büyürse test başarısız olur.

## Lisans servisi

İki uç nokta: biri token üretir, biri onu kontrol edecek genel anahtarı yayımlar.

**Çevrimdışı doğrular.** Token, Ed25519 ile imzalanmış 90 günlük bir mühlettir ve pakete gömülü bir anahtara karşı kontrol edilir. Bu servisin çökmüş, yavaş, erişilemez ya da yok olmuş olması derlemelerinizi durdurmaz. Bir derlemeyi bozabilen bir lisans sunucusu, en kötü anda, bize para ödeyen bir müşteri için bunu yapacaktır.

**Ne saklar:** lisans anahtarının özeti, katman, koltuk sayısı, hesap ve aktive olmuş makine parmak izlerinin tuzlanmış özetleri.

**Ne saklamaz:** ana bilgisayar adı, IP adresi, depo adı, proje adı ya da neyi değerlendirdiğinize dair hiçbir şey. Kit bunları göndermez ve şemanın onları koyacağı bir yer yoktur. Bu yokluk bir tasarım taahhüdüdür — "bunu tutmuyorsunuz" sorusunu yanıtlayabilmenin en ucuz yolu, tutacak bir yerin olmamasıdır.

Parmak izi **sizin makinenizde** hesaplanır ve saklanmadan önce tuzlanır. Ham makine kimliği makineden hiç çıkmaz.

## Raporlar ve defter

Raporlar ve denetim zinciri deponuzdaki dosyalardır. Onlara siz sahipsiniz, silebilirsiniz ve biz okuyamayız.

Raporlar **sınıfları ve sayıları kaydeder, asla değerleri**. Tespit ettiği kişisel veriyi saklayan bir maskeleme kaydı, maskelemenin önlemek için var olduğu başarısızlıktır — bu yüzden maskeleme, çağırana bırakılmayıp rapor serileştirilirken uygulanır.

## Konsol

Statik bir dışa aktarım. Ona gösterdiğiniz bir JSON raporunu gösterir. Sunucusu, kimlik doğrulaması, veritabanı ve kod tabanında hiçbir yazma yolu yoktur — dil ve tema düğmeleri sakladığı tek şeydir ve onları da kendi tarayıcınızda saklar.

## Alt işleyiciler

Lisans ve telemetri servisleri için: bir konteyner barındırıcısı ve yönetilen bir Postgres örneği, ikisi de AB'de (Amsterdam). Başka hiçbir şey. Müşteri rapor verisi alan hiçbir şey işletmiyoruz, dolayısıyla bunu alabilecek bir alt işleyici de yok.

## İletişim

`privacy@atheros.ai`
