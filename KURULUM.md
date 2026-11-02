# Atama İzleyici

3 kamu sitesini 15 dakikada bir kontrol eder, yeni içerik çıkınca ntfy ile telefona bildirim gönderir.

## Kurulum
1. Telefona **ntfy** uygulamasını kur ve kendi konu adına abone ol.
2. Depoda Settings → Secrets and variables → Actions altında `NTFY_TOPIC` secret'ını ekle (değer: konu adın).
3. Actions sekmesi → Atama Izleyici → Run workflow ile ilk çalıştırmayı yap.

İlk çalıştırma sadece mevcut içeriği kaydeder, sonrasında yalnızca yeni çıkanlar bildirilir.
Bir site 3 kez üst üste okunamazsa uyarı bildirimi gelir.
