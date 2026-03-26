# Jira Monitor - Proje Analizi

**Tarih:** 26 Mart 2026  
**Proje Adı:** Jira Monitor  
**Dil:** Python 3  
**UI Framework:** Tkinter  
**Versiyon:** 1.0.0

---

## 📋 Proje Özeti

Jira Monitor, Jira REST API'sini kullanarak masaüstü ortamında issue'ları izlemek ve yönetmek için geliştirilmiş bağımsız bir Python uygulamasıdır. Türkçe arayüzü ve modern tasarımı ile kullanıcı dostu bir deneyim sunmaktadır.

---

## 🏗️ Proje Yapısı

```
JiraMonitor/
├── monitor.py                 # Ana uygulama (1417+ satır)
├── run.sh                     # Linux/Mac çalıştırma scripti
├── run.bat                    # Windows çalıştırma scripti
├── push.sh                    # Versiyon artırma ve push scripti
├── fix_encoding.py            # Encoding kontrol aracı
├── install/
│   ├── install.sh             # Linux/Mac kurulum scripti
│   ├── install.bat            # Windows kurulum scripti
│   └── .venv/                 # Kurulum sırasında oluşturulan venv
├── .venv/                     # Aktif virtual environment
├── .version                   # Versiyon numarası (major.minor.patch.tarih)
├── .gitignore                 # Git ignore kuralları
├── PROJE_ANALIZI.md           # Bu dokümantasyon
└── __pycache__/               # Python cache dosyaları
```

---

## 🔧 Teknik Mimarı

### Sınıflar ve Modüller

#### 1. **JiraClient** (Satır 20-180)
Jira REST API ile iletişim kuran istemci sınıfı.

**Özellikler:**
- Basic Authentication (username + API token)
- HTTP istekleri (GET, POST, PUT)
- JQL (Jira Query Language) desteği
- 30 saniye timeout

**Metodlar:**
- `search_issues()` - JQL ile issue arama
- `get_issue()` - Tek issue detayı
- `get_issue_comments()` - Issue yorumları
- `add_comment()` - Yorum ekleme
- `update_comment()` - Yorum güncelleme
- `get_attachments()` - Dosya ekleri
- `get_current_user()` - Giriş yapan kullanıcı
- `assign_issue()` - Issue atama
- `update_issue_description()` - Açıklama güncelleme
- `download_attachment()` - Dosya indirme

#### 2. **ConfigManager** (Satır 182-220)
Uygulama ayarlarını yönetir.

**Depolama:** `~/.jira_monitor_config.json`

**Varsayılan Ayarlar:**
```json
{
  "server_url": "https://jira.gelirler.gov.tr",
  "username": "",
  "api_token": "",
  "refresh_interval": 120,
  "default_users": "haktan.atamer,ayse.aydogdu,...",
  "default_projects": "EVDBS,EPDK,Vedop3_VT,KONF",
  "default_status": "OPEN,'In Progress',Reopened",
  "extra_projects": "",
  "extra_statuses": "",
  "assign_queue": [],
  "assign_queue_index": 0
}
```

#### 3. **SettingsDialog** (Satır 222-380)
Ayarlar penceresi (Tkinter Toplevel).

**Sekmeler:**
- **Bağlantı:** Sunucu URL, kullanıcı adı, API token
- **Filtreler:** Yenileme süresi, varsayılan kullanıcılar/projeler/statuslar, ek projeler/statuslar
- **Atama Kuyruğu:** Round-robin atama listesi (yukarı/aşağı/sil/sıfırla)

#### 4. **IssueDetailDialog** (Satır 450-900)
Issue detay penceresi (Tkinter Toplevel).

**Sekmeler:**
- **Detaylar:** Issue bilgileri (status, assignee, priority vb.) ve açıklama
- **Yorumlar:** Mevcut yorumlar ve yeni yorum ekleme
- **Dosya Ekleri:** Ekleri görüntüleme/indirme

**Özellikler:**
- Jira wiki markup render etme
- Açıklama düzenleme (diff gösterimi)
- Yorum düzenleme (sadece kendi yorumları)
- Dosya indirme ve açma
- Tarayıcıda açma

#### 5. **JiraMonitorApp** (Satır 1050-1417)
Ana uygulama sınıfı.

**Özellikler:**
- Tkinter GUI
- Treeview ile issue listesi
- Filtreler (kullanıcı, proje, status)
- Otomatik yenileme (threading)
- Round-robin issue atama
- Modern stil (clam theme)

---

## 🎨 Arayüz Bileşenleri

### Ana Pencere
- **Başlık:** "Jira Monitor" + issue sayısı
- **Filtreler:** Kullanıcı, Proje, Status combobox'ları
- **Butonlar:** Yenile, Ayarlar
- **Treeview:** Issue listesi (9 kolon)
- **Status Bar:** Son güncelleme zamanı

### Treeview Kolonları
1. `#` - Sıra numarası
2. `Key` - Issue anahtarı (PROJE-123)
3. `Summary` - Başlık
4. `Status` - Durum
5. `Assignee` - Atanan kişi
6. `Project` - Proje adı
7. `Updated` - Son güncelleme tarihi
8. `Created` - Oluşturma tarihi
9. `Ata` - Round-robin atama butonu

### Renk Kodlaması
- **Açık Mavi:** EVDBS projesi
- **Turuncu:** EPDK projesi
- **Bej:** Yazılım Destek
- **Açık Yeşil:** Bugün güncellenen issue'lar

---

## 🔄 İş Akışları

### 1. Uygulama Başlatma
```
run.sh → .venv/bin/activate → python3 monitor.py
```

### 2. Jira Bağlantısı
```
ConfigManager.load_config() 
  → JiraClient(server_url, username, api_token)
  → test_search_issues() (bağlantı testi)
  → _populate_filters() (combobox'ları doldur)
```

### 3. Issue Yükleme
```
_load_issues()
  → JQL oluştur (filtreler + varsayılan değerler)
  → jira_client.search_issues(jql)
  → Treeview'e ekle
  → Renk kodlaması uygula
```

### 4. Issue Detayı Görüntüleme
```
Double-click on Treeview
  → IssueDetailDialog açılır
  → get_issue() + get_issue_comments() + get_attachments()
  → Jira markup render edilir
```

### 5. Round-Robin Atama
```
"Ata" butonuna tıkla
  → assign_queue[assign_queue_index] kullanıcısı seçilir
  → assign_issue(issue_key, username)
  → assign_queue_index artırılır (% queue.length)
  → Ayarlar kaydedilir
```

### 6. Otomatik Yenileme
```
_start_refresh() (threading)
  → Her refresh_interval saniyede
  → _load_issues() çağrılır
```

---

## 📝 Önemli Fonksiyonlar

### Jira Markup Render Etme
- `render_jira_markup()` - Jira wiki markup'ı Tkinter Text widget'ına render eder
- `_insert_inline()` - Satır içi markup'ı (bold, italic, link vb.) işler

**Desteklenen Markup:**
- `*bold*` - Kalın
- `_italic_` - İtalik
- `+underline+` - Altı çizili
- `-strike-` - Üstü çizili
- `{{monospace}}` - Monospace
- `[text|url]` - Link
- `[~username]` - Kullanıcı referansı
- `h1. h2. h3.` - Başlıklar
- `* - #` - Listeler
- `||header||` - Tablo başlığı
- `|cell|` - Tablo hücresi
- `{code}...{code}` - Kod bloğu

### Dosya İşlemleri
- `_open_attachment()` - Dosya açma/indirme
- `_open_file()` - OS'a göre dosyayı varsayılan uygulamayla aç

**Görüntülenebilir Türler:** PDF, PNG, JPG, GIF, BMP, SVG, TXT, LOG, XML, JSON, HTML, DOC, DOCX, XLS, XLSX, PPT, PPTX

---

## 🔐 Güvenlik

- **Authentication:** Basic Auth (base64 encoded)
- **API Token:** Şifreli gösterilir (show="*")
- **Timeout:** 30 saniye (indirme 60 saniye)
- **Hata Yönetimi:** HTTP hataları ve bağlantı sorunları yakalanır

---

## 🚀 Kurulum ve Çalıştırma

### Linux/Mac
```bash
cd JiraMonitor
./install/install.sh
./run.sh
```

### Windows
```cmd
cd JiraMonitor
install\install.bat
run.bat
```

### Gereksinimler
- Python 3.8+
- tkinter (genellikle Python ile birlikte gelir)
- urllib (standart kütüphane)
- json (standart kütüphane)
- threading (standart kütüphane)

---

## 📊 Veri Akışı

```
Jira Server
    ↓
JiraClient (REST API)
    ↓
ConfigManager (JSON config)
    ↓
JiraMonitorApp (Main UI)
    ├── SettingsDialog (Ayarlar)
    ├── IssueDetailDialog (Detaylar)
    └── Treeview (Issue Listesi)
```

---

## 🎯 Temel Özellikler

✅ **Yapılan İşler:**

1. **Jira Entegrasyonu**
   - REST API v2 desteği
   - JQL sorguları
   - Basic authentication

2. **Issue Yönetimi**
   - Issue arama ve filtreleme
   - Detay görüntüleme
   - Açıklama düzenleme
   - Yorum ekleme/düzenleme
   - Dosya ekleri indirme

3. **Atama Sistemi**
   - Round-robin otomatik atama
   - Atama kuyruğu yönetimi
   - Sıradaki kullanıcı gösterimi

4. **Arayüz**
   - Modern Tkinter tasarımı
   - Türkçe dil desteği
   - Renk kodlaması
   - Responsive layout

5. **Otomasyon**
   - Otomatik yenileme (threading)
   - Jira markup render etme
   - Dosya açma (OS entegrasyonu)

6. **Yapılandırma**
   - JSON tabanlı ayarlar
   - Kullanıcı/proje/status filtreleri
   - Atama kuyruğu özelleştirmesi

---

## 📌 Notlar

- Uygulama tam ekran modunda başlar
- Ayarlar `~/.jira_monitor_config.json` dosyasında saklanır
- Threading kullanılarak UI donmaz
- Jira wiki markup desteği kapsamlı
- Dosya indirme geçici klasöre yapılır

---

## 🔗 Bağlantılar

- **Jira Server:** https://jira.gelirler.gov.tr
- **Varsayılan Projeler:** EVDBS, EPDK, Vedop3_VT, KONF
- **Varsayılan Kullanıcılar:** 12 kişi (haktan.atamer, ayse.aydogdu, vb.)

---

**Proje Analizi Tamamlandı**


---

## 🔄 Güncelleme - "Bana Ata" Düğmesi

**Tarih:** 23 Mart 2026 - 10:41

### Yapılan Değişiklikler:

#### 1. **Düğme Değiştirildi**
- "👤 Ata" → "👤 Bana Ata"
- Komut: `_assign_from_dialog` → `_assign_to_me`

#### 2. **Yeni Metod: `_assign_to_me()`**
```python
def _assign_to_me(self):
    """Issue'yu bağlı kullanıcıya ata"""
    # Bağlı kullanıcı bilgisini al (current_user)
    # Onay dialog'u göster
    # Jira API'ye atama isteği gönder
    # Başarılı mesajı göster
```

### 🎯 Kullanıcı Deneyimi

1. Issue detay penceresinde "👤 Bana Ata" butonuna tıkla
2. Onay dialog'u gösterilir (bağlı kullanıcı adı gösterilir)
3. Onaylarsan → Issue sana atanır
4. Başarılı mesajı gösterilir

### ✅ Farklar

- **Eski:** Kullanıcı seçme dialog'u
- **Yeni:** Direkt atama (bağlı kullanıcıya)
- **Hız:** Tek tıkla atama yapılır
- **Eski:** Kullanıcı seçme dialog'u
- **Yeni:** Direkt atama (bağlı kullanıcıya)
- **Hız:** Tek tıkla atama yapılır

---

## 🔄 Versiyon Yönetimi

Uygulama otomatik versiyon yönetimi ile çalışır. Her push işlemi için `push.sh` script'i kullanılır:

```bash
./push.sh
```

**Script'in Yapıkları:**
1. `.version` dosyasından mevcut versiyonu okur
2. Patch versiyonu 1 artırır
3. Tarih saat ekler (YYYYMMDDHHMM formatında)
4. `monitor.py`'de `__version__` günceller
5. `.version` ve `monitor.py` dosyalarını commit eder
6. Git push yapar

**Versiyon Formatı:** `1.0.0.202603261725`

---

## 📊 Veri Akışı

```
Jira Server
    ↓
JiraClient (REST API)
    ↓
ConfigManager (JSON config)
    ↓
JiraMonitorApp (Main UI)
    ├── SettingsDialog (Ayarlar)
    ├── IssueDetailDialog (Detaylar)
    └── Treeview (Issue Listesi)
```

---

## 🎯 Temel Özellikler

✅ **Yapılan İşler:**

1. **Jira Entegrasyonu**
   - REST API v2 desteği
   - JQL sorguları
   - Basic authentication

2. **Issue Yönetimi**
   - Issue arama ve filtreleme
   - Detay görüntüleme
   - Açıklama düzenleme
   - Yorum ekleme/düzenleme
   - Dosya ekleri indirme

3. **Atama Sistemi**
   - Round-robin otomatik atama
   - Atama kuyruğu yönetimi
   - Sıradaki kullanıcı gösterimi

4. **Arayüz**
   - Modern Tkinter tasarımı
   - Türkçe dil desteği
   - Renk kodlaması
   - Responsive layout

5. **Otomasyon**
   - Otomatik yenileme (threading)
   - Jira markup render etme
   - Dosya açma (OS entegrasyonu)

6. **Yapılandırma**
   - JSON tabanlı ayarlar
   - Kullanıcı/proje/status filtreleri
   - Atama kuyruğu özelleştirmesi

---

## 📌 Notlar

- Uygulama tam ekran modunda başlar
- Ayarlar `~/.jira_monitor_config.json` dosyasında saklanır
- Threading kullanılarak UI donmaz
- Jira wiki markup desteği kapsamlı
- Dosya indirme geçici klasöre yapılır

---

## 🔗 Bağlantılar

- **Jira Server:** https://jira.gelirler.gov.tr
- **Varsayılan Projeler:** EVDBS, EPDK, Vedop3_VT, KONF
- **Varsayılan Kullanıcılar:** 12 kişi (haktan.atamer, ayse.aydogdu, vb.)

---

**Proje Analizi Tamamlandı**
