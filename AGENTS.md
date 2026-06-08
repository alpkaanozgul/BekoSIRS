# BekoSIRS — Codex Proje Kılavuzu

## Proje Özeti
BekoSIRS, Beko KKTC için geliştirilmiş tam yığın e-ticaret yönetim sistemidir. Ürün, kategori, servis talebi, teslimat, taksit planı ve ML tabanlı öneri sistemlerini kapsar.

- **GitHub:** `sutozremzi/BekoSIRS`
- **Dil:** Türkçe (UI ve dokümantasyon)

---

## Dizin Yapısı

```
BekoSIRS/
├── BekoSIRS_api/          # Django REST backend (Python 3.11+)
├── BekoSIRS_Web/          # React web paneli (TypeScript + Vite)
├── BekoSIRS_Frontend/     # React Native mobil uygulama (Expo)
├── .github/workflows/     # CI/CD (ci.yml)
├── docker-compose.yml     # Dockerized deployment
├── start-all.sh           # Tek komutla başlatma scripti
└── AGENTS.md              # Bu dosya
```

---

## Geliştirme Komutları

### Backend (BekoSIRS_api)
```bash
cd BekoSIRS_api
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### Web Paneli (BekoSIRS_Web)
```bash
cd BekoSIRS_Web
npm install
npm run dev -- --host           # http://localhost:5173
npm run build                   # Production build
```

### Mobil Uygulama (BekoSIRS_Frontend)
```bash
cd BekoSIRS_Frontend
npm install
npx expo start                  # ios/android/web seç
npm run android
npm run ios
```

### Tüm Platformları Başlat
```bash
./start-all.sh                  # Backend + Web
./start-all.sh --backend-only
./start-all.sh --web-only
./start-all.sh --mobile-only
./start-all.sh --stop
```

---

## Test Komutları

### Backend
```bash
cd BekoSIRS_api
pytest                          # Tüm testler
pytest --cov                    # Coverage raporu (min %25)
```

### Web
```bash
cd BekoSIRS_Web
npm test                        # Vitest
npm run test:coverage
```

### Mobil
```bash
cd BekoSIRS_Frontend
npm test                        # Jest (--passWithNoTests)
```

---

## Teknoloji Stack

| Platform | Framework | Dil | Test |
|----------|-----------|-----|------|
| Backend | Django 4.2 + DRF | Python 3.11+ | pytest |
| Web | React 19 + Vite 5 | TypeScript | Vitest |
| Mobil | React Native 0.81 + Expo 54 | TypeScript | Jest |

**Backend Kütüphaneler:**
- Auth: `djangorestframework-simplejwt`
- API Docs: `drf-spectacular` → http://localhost:8000/api/schema/swagger-ui/
- ML: scikit-learn, DeepFace, pandas, numpy
- DB: Django ORM → SQLite (dev) / PostgreSQL Supabase (prod)
- Production: gunicorn, WhiteNoise, Sentry

**Web Kütüphaneler:**
- Routing: React Router DOM 7
- HTTP: Axios
- Harita: React Leaflet, @react-google-maps/api
- Grafik: Recharts
- Stil: Tailwind CSS 3

**Mobil Kütüphaneler:**
- Routing: Expo Router 6
- Biyometrik: expo-local-authentication (Face ID / Touch ID)
- Kamera: expo-camera
- Harita: react-native-maps
- Auth: expo-secure-store, JWT

---

## API Endpoints

- **Base URL:** http://localhost:8000/api/v1/
- **Swagger:** http://localhost:8000/api/schema/swagger-ui/
- **Health:** http://localhost:8000/api/v1/health/

Ana endpoint grupları: auth (token/refresh), users, products, categories, reviews, service-requests, deliveries, installment-plans, recommendations, notifications, biometric

---

## Ortam Değişkenleri

### Backend (BekoSIRS_api/.env)
```
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=postgresql          # veya sqlite3
DB_NAME=, DB_USER=, DB_PASSWORD=, DB_HOST=, DB_PORT=
CORS_ALLOWED_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
```

### Mobil (BekoSIRS_Frontend/.env)
```
EXPO_PUBLIC_API_URL=http://192.168.x.x:8000/   # dev (cihazın IP'si)
EXPO_PUBLIC_PROD_API_URL=https://api.bekosirs.com/
```

---

## CI/CD (GitHub Actions)

**Dosya:** `.github/workflows/ci.yml`
**Tetikleyici:** `main` branch'e push/PR

| Job | Araç | Notlar |
|-----|------|--------|
| backend | pytest | Ephemeral PostgreSQL 15, coverage ≥%25 |
| web | Vitest | TypeScript check + build |
| mobile | Jest | `--passWithNoTests` flag |
| deploy | artifact | Web build → 30 gün saklanır |

---

## Mimari Notlar

- **ML Öneri Sistemi:** NCF (Neural Collaborative Filtering) + Content-based + Popularity hybrid (`BekoSIRS_api/products/ml_recommender.py`, ~900 satır)
- **Biyometrik:** DeepFace ile Face ID tabanlı giriş (`biometric/` endpoints)
- **Rota Optimizasyonu:** `products/services/route_optimizer.py`
- **CI'dan Hariç Tutulan Testler:** notifications, installments, biometric (CI'da skip edilir)
- **Adres Yapısı:** KKTC bölgelerine özel

---

## Docker

```bash
docker-compose up --build      # API (8000) + Web (3000)
docker-compose down
```

---

## Önemli Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `BekoSIRS_api/products/models.py` | Ana DB modelleri (~38KB) |
| `BekoSIRS_api/products/serializers.py` | DRF serializers (~37KB) |
| `BekoSIRS_api/products/ml_recommender.py` | ML motoru (~47KB) |
| `BekoSIRS_api/bekosirs_backend/settings.py` | Django ayarları |
| `BekoSIRS_Web/src/App.tsx` | Web routing |
| `BekoSIRS_Frontend/app/_layout.tsx` | Mobil root layout |
| `.github/workflows/ci.yml` | CI/CD pipeline |
