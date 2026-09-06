# Hızlı başlangıç
> pip install'dan zincir özetli bir uyum raporuna beş dakikada, çevrimdışı.

# Hızlı başlangıç

API anahtarı yok. Ağ yok. Vektör deposu yok. Aşağıdakilerin hepsi bir tünelde dizüstü bilgisayarda çalışır.

## Kurulum

```
pip install atheros-compliance-kit
atheros-kit doctor
```

`doctor`, neyin kurulu olduğunu, hangi model sağlayıcıları için anahtar tuttuğunuzu ve dolayısıyla her kontrolün hangi yolu izleyeceğini yazdırır. Anahtar yokken her şey deterministik yolunu izler — bu desteklenen varsayılandır, bozuk bir durum değil.

## 1. Bir sistemi sınıflandırın

```
atheros-kit euact classify \
  --name TalentFlow --sector hr \
  --use-case "cv screening" --use-case "candidate ranking" --lang tr
```

```
HIGH  TalentFlow   güven 0.85   EU-2024/1689:2024-07-12
    · kullanım senaryosu Annex III 4. Employment and worker management ile eşleşiyor
    · yüksek riskli bir sektörde konuşlandırılmış: hr
  maddeler: Annex III, Art. 6(2)
  dayanak   indicator_matched
```

Madde atıfları her iki dilde de bilerek `Art. 6(2)` kalır: atıfları yazımı değişen iki dilli bir kanıt paketi çapraz eşleştirilemez.

## 2. LLM istemcinizi sarın

`GuardedClient` bir SDK'yı değil bir **çağrılabiliri** sarar — böylece her sağlayıcıyla çalışır ve o sağlayıcı istemci nesnesini değiştirdiğinde çalışmaya devam eder.

```python
from atheros_kit import GuardedClient, GuardPolicy, CustomEntity

client = GuardedClient(
    call=lambda prompt: openai_client.responses.create(...).output_text,
    policy=GuardPolicy(
        custom_entities=[CustomEntity("CODENAME", literals=["Project Northwind"])],
        static_fallback="Bu isteği güvenli biçimde tamamlayamadık.",
    ),
    model_name="gpt-5-2025-08-07",
)

result = client.invoke("ali@acme.com için özetle, IBAN NL91ABNA0417164300")
result.text              # çıkışta maskelenir, dönüşte geri konur
result.degraded          # bir şey yedeğe düştüyse True — asla sessiz değil
result.masked_entities   # {"EMAIL": 1, "IBAN": 1} — sınıf ve sayı, asla değer
```

`GuardPolicy.observe()` ile başlayın: her şeyi ölçer, hiçbir şeyi engellemez — böylece katı bir politikanın neyi durduracağını, üretimde durdurmadan önce görürsünüz.

## 3. Bir külliyatı denetleyin

```python
from atheros_kit.rag import RAGAuditEngine

audit = RAGAuditEngine.from_store("chroma", collection_name="bilgi-tabani").run()
audit.fairness_score       # 0-100, değerlendirilen boyutlar üzerinden harmonik
audit.quality_score        # yinelemeler, gömmesizler, boyutlandırma, kişisel veri
audit.bias.unassessable    # ← bunu okuyun
print(audit.remediation_markdown("tr"))
```

Desteklenen bir depo yok mu? Kendiniz okuyun. Bu yol yedek değil, birinci sınıf bir yoldur:

```python
from atheros_kit.rag import RAGAuditEngine, Chunk
RAGAuditEngine(chunks=[Chunk(id, text, vector) for ...]).run()
```

Bağlantı kurgusu gereği salt okunurdur. İyileştirme, bir insanın çalıştıracağı tarifler üretir; Kit külliyatınızı asla değiştirmez.

## 4. Bir satıcıyı değerlendirin

```
atheros-kit vendor assess openai --region EU --lang tr
```

Satıcının web sitesinin söylediğini değil, kendi sözleşmenizin ve konsolunuzun gösterdiğini geçirin:

```python
from atheros_kit.vendor import assess
assess("openai", required_regions=["EU"],
       contract_flags={"training_optout_enabled": True,
                       "training_optout_contractual": True})
```

Mevcut, etkin ve sözleşmesel üç farklı olgudur. Var olan ama kapalı bir çıkma seçeneği hiçbir şeyi korumaz ve rapor bunların hangisine sahip olduğunuzu söyler.

## 5. Derlemeyi başarısız kılın

```
atheros-kit init --ci github     # atheros.yml ve çalışan bir iş akışı yazar
atheros-kit ci gate              # çıkış 0 geçti · 1 başarısız · 2 hata
```

İş akışı özeti pull request'e yorum olarak yazar ve kanıtı yükler — kapı kırmızıya döndüğünde de, ki asıl önemli olan odur.

## 6. Defteri doğrulayın

```
atheros-kit audit verify
```

```
sağlam  8 kayıt: .atheros/audit_trail.jsonl
```

O dosyanın bir baytını değiştirip yeniden çalıştırın. Demo bundan ibarettir.

## Sonraki adım

- [Bu aracın size söylemediği şeyler](honesty.html) — herhangi bir skora göre hareket etmeden önce okuyun
- [Modüller](modules.html) — tam referans
- [CI kapısı](ci.html) — eşikler ve şablonlar
- [Gizlilik](privacy.html) — neyi toplamadığımız ve nasıl kontrol edeceğiniz
