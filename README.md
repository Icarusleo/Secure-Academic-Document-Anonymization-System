# Secure Academic Document Anonymization System

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)
![Framework](https://img.shields.io/badge/framework-Django%20%2F%20Flask-orange.svg)

Bu proje, akademik belgelerdeki (makale, rapor, ödev vb.) kişisel verileri (PII - Personally Identifiable Information) tespit eden ve bu verileri güvenli bir şekilde maskeleyerek dokümanları anonim hale getiren bir sistemdir. KVKK ve GDPR uyumluluğu gözetilerek geliştirilmiştir.

## 🚀 Özellikler

- **Otomatik PII Tespiti:** NLP (Doğal Dil İşleme) kullanarak isim, e-posta, telefon numarası ve kurum bilgilerini algılar.
- **Çoklu Format Desteği:** `.pdf`, `.docx` ve `.txt` uzantılı akademik dosyaları işleyebilir.
- **Güvenli Maskeleme:** Hassas verileri yıldızlama (masking) veya etiketleme (redaction) yöntemleriyle gizler.
- **Kullanıcı Paneli:** Dosya yükleme, işlem geçmişi ve sonuçları indirme imkanı sunan web arayüzü.
- **Akademik Odak:** Kaynakça ve atıf dizinlerini bozmadan sadece yazar/öğrenci bilgilerine odaklanma.

## 🛠️ Kullanılan Teknolojiler

- **Backend:** Python (Django / Flask)
- **NLP Kütüphaneleri:** Spacy / NLTK / Presidio
- **Dosya İşleme:** PyMuPDF (fitz), python-docx
- **Frontend:** HTML5, CSS3, JavaScript (Bootstrap)
- **Veritabanı:** SQLite / PostgreSQL

## 📂 Proje Yapısı

```text
yazlab2_1/
└── myproject/
    ├── core/                # Ana uygulama mantığı ve NLP modülleri
    ├── media/               # Yüklenen ve işlenen dokümanlar
    ├── static/              # CSS, JS ve görsel dosyaları
    ├── templates/           # HTML arayüzleri
    ├── manage.py            # Django yönetim dosyası
    └── requirements.txt     # Gerekli kütüphaneler listesi
