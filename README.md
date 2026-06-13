# 🚀 MatchRecord FastAPI Backend Engine

Bu proje, halı saha akıllı maç kayıt ve video analiz ekosisteminin merkezi veri yönetim ve kimlik doğrulama (Authentication) sunucusudur. Saha içindeki **STM32 & ESP8266** donanım katmanından gelen anlık gol/zaman damgası verilerini güvenli bir şekilde işler, veritabanına kaydeder ve **Qt6 C++ Masaüstü İstemcisi**ne API uç noktaları (endpoints) üzerinden servis eder.

---

## 🛠️ Temel Özellikler

* **Yüksek Performanslı Asenkron Mimari:** Python'un en hızlı web çatılarından biri olan FastAPI ve `asyncio` tabanlı non-blocking G/Ç (I/O) yapısı.
* **OAuth2 Tabanlı Güvenli Yetkilendirme:** Kullanıcı giriş ve kayıt işlemlerinde JWT (JSON Web Token) tabanlı güvenli kimlik doğrulama mekanizması.
* **Donanım Dostu İletişim:** ESP8266 gibi gömülü sistemlerin bellek sınırlarına uygun, hafif (lightweight) JSON veri kabul yapısı.
* **İlişkisel Veri Yönetimi:** SQLite / SQLAlchemy ORM mimarisi kullanılarak optimize edilmiş ilişkisel tablolar.

---

## 🏗️ Veritabanı Şeması (Database Models)

Sistem, veri tutarlılığını korumak amacıyla tasarlanmış iki temel ilişkisel tablodan oluşur:

### 1. `users` (Üye / Kullanıcı Tablosu)
Sisteme erişim yetkisi olan teknik personeli veya saha yöneticilerini tutar.
* `id`: Benzersiz kullanıcı ID'si (Primary Key)
* `username`: Benzersiz kullanıcı adı
* `email`: Kullanıcı maili
* `pitch_count`: Kullanıcının sahip olduğu saha sayısı
* `hashed_password`: Güvenli şekilde şifrelenmiş parola
* `image_file`: Gelecekte olabilecek bir blog yapısı için kullanıcı image yolu

### 2. `records` (Zaman Damgaları / Olay Günlüğü Tablosu)
Saha içindeki donanımdan tetiklenen veya arayüzden manuel eklenen tüm önemli anları kronolojik olarak saklar.
* `id`: Otomatik artan kayıt ID'si (Primary Key)
* `pitch_id`: Zaman kaydının eşleştiği saha id si
* `team_id`: Zaman kaydının eşleştiği takım id si
* `datetime_from_st`: Stm32 nin gönderdiği zaman(string olarak) (örn:`25/4/26 12:23:23`) 
* `user_id`: kullanıcı id si
* `date_posted`: Olayın database geçtiği gerçek zaman damgası (stm32 den gelenle karşılaştırıp scoreboard saatinin doğruluğu teyit edilebilir)(örn:`2026-06-09 09:23:12.463724`)

---

## 🔌 API Uç Noktaları (Endpoints)

### 🔐 Kimlik Doğrulama & Kullanıcı Yönetimi
* `POST /api/users` -> Yeni kullanıcı kaydı oluşturur (Şifreleri hash'leyerek saklar).
* `POST /api/auth/login` -> Giriş bilgilerini doğrular ve JWT erişim token'ı üretir.
* `GET /api/users/{user_id}` -> User id ye göre kullanıcı bilgilerini verir(user authentication bekler).

### ⚽ Maç Kayıtları Yönetimi (Records API)
* `POST /api/records` -> Veritabanına zaman kaydını gönderir (Qt istemcisi burayı dinler)(**ESP8266 Wi-Fi** modülü gol anlarında bu uca veri basar).
* `GET /api/records/{user_id}/{pitch_id}` -> Kullanıcı id,saha id ve istenilen maç saati verilince o maçın katılarını alırsın(Qt istemcisi burayı dinler)(user authentication bekler).

---

## 🛠️ Kurulum ve Çalıştırma

### 1. Gereksinimler
* Python 3.10 veya üzeri
* Pip (Python Paket Yöneticisi)

### 2. Bağımlılıkların Kurulması
Projeyi klonladıktan sonra kök dizinde sanal bir ortam oluşturun ve gerekli paketleri yükleyin:

```bash
# Sanal ortam oluşturma
python3 -m venv venv
source venv/bin/activate 

# Bağımlılıkları yükleme
pip install -r requirements.txt
```

Not: Eğer requirements.txt dosyanız henüz yoksa, projenizde şu paketlerin kurulu olduğundan emin olun:
```bash
pip install fastapi uvicorn sqlalchemy passlib[bcrypt] pyjwt python-multipart
```

### 3. Sunucuyu Başlatma

Geliştirme sunucusunu yerel ağda veya sunucuda ayağa kaldırmak için:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
* `--host 0.0.0.0` parametresi, yerel ağdaki ESP8266 modülünün ve Qt uygulamasının sunucuya doğrudan IP adresi üzerinden erişebilmesini sağlar.

### 📖 İnteraktif API Dokümantasyonu

Fastapinin sğladığı dökümantasyon sayfası ile urllerin çalışma mantığını detaylı inceleyip test edebilisiniz.

 * http://localhost:8000/docs

