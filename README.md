# Modern Bangladesh E-Commerce + ERP + Machine Learning Platform

Production-oriented monorepo for businesses operating in Bangladesh.

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS, Recharts, TanStack Query ready |
| Backend | Python 3.12, FastAPI, Pydantic, Motor (async MongoDB) |
| Database | MongoDB (local or Atlas) |
| Auth | Separate Customer vs Admin JWT, TOTP 2FA, RBAC, audit logs |
| Payments | COD (full), bKash / Nagad / Rocket adapter architecture |
| ML | Demand forecast, Product Intelligence Score, smart purchase recommendations |
| Infra | Docker Compose, Nginx-ready |

## Quick start

### 1. MongoDB
```bash
# local
docker run -d -p 27017:27017 --name mongo mongo:7
# or use Atlas and set MONGODB_URI
```

### 2. Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # already has a .env for dev
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Seed demo data
```bash
cd backend
python ../scripts/seed.py
```
- **Main Admin**: `admin@example.com` / `Admin@12345`
- **Customer**: `customer1@example.bd` / `Customer@123`

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```
- Storefront: http://localhost:3000  
- Admin ERP: http://localhost:3000/admin/login  

### 5. Docker (all services)
```bash
docker compose up --build
```

## Security model (as specified)

- **Customer tokens never work on admin routes** (token `type` claim enforced).
- **Admin login flow**: email → password → 2FA (TOTP) → JWT with role + permissions.
- **Main Admin** has all permissions and cannot be disabled/deleted by normal admins.
- Lower admins cannot escalate their own role or create Main Admin.
- Every sensitive action is written to `audit_logs`.

## Key API groups

```
/api/v1/auth/customer/*
/api/v1/auth/admin/*
/api/v1/admins/*
/api/v1/products , /api/v1/categories
/api/v1/orders/*
/api/v1/payments/*
/api/v1/analytics/*
/api/v1/ml/*
```

## ML capabilities included

- 7 / 30 / 90 day demand forecast per product (moving-average + trend; XGBoost-ready)
- Smart purchase recommendations (stock vs predicted demand)
- Product Intelligence Score (0–100) with labels
- Business Intelligence Center endpoints (top profit products, low-stock alerts, auto insights)

## Bangladesh localization

- Currency: BDT / ৳  
- Phone validation for BD mobile numbers  
- Address: Division → District → Upazila  
- Payment methods: COD, bKash, Nagad, Rocket  
- Timezone: Asia/Dhaka  

## Extending

1. Add real bKash/Nagad credentials in `.env` and complete the provider classes in `app/api/v1/payments.py`.
2. Replace the simple forecast with XGBoost/LightGBM training jobs under `ml/training/` and Celery workers.
3. Expand the Next.js admin pages (orders table, product form, inventory transfers, invoice PDF).
4. Wire React Query + Zustand for cart and auth state.

## Project layout

```
ecommerce-erp/
  backend/          # FastAPI
  frontend/         # Next.js
  ml/               # datasets, training, models
  scripts/          # seed
  infrastructure/   # docker, nginx
  docs/
  docker-compose.yml
```

Built to be a real foundation, not a static demo — start the services, seed data, and the ERP dashboard + ML recommendations become usable immediately.
