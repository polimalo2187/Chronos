# Chronos Backend (FastAPI + Mongo Atlas) — Railway-ready

Este repo es el backend base de **Chronos**. Incluye:
- Registro/Login (JWT)
- Roles (user/admin)
- Planes (free/plus/premium) + expiración
- Vinculación segura con Telegram usando **@CRNAssistant_bot** (link-code)
- Endpoints admin para activar planes
- Healthcheck

## 1) Variables de entorno (Railway → Variables)

Obligatorias:
- `MONGODB_URI` = URI de Mongo Atlas (mongodb+srv://...)
- `JWT_SECRET` = string largo aleatorio

Recomendadas:
- `JWT_EXPIRE_MINUTES` = 43200 (30 días)
- `TELEGRAM_BOT_USERNAME` = CRNAssistant_bot
- `TELEGRAM_LINK_SECRET` = string largo (para proteger /telegram/link)

Bootstrap admin (opcional, recomendado):
- `ADMIN_EMAIL` = tu correo admin
- `ADMIN_PASSWORD` = tu password admin

## 2) Deploy en Railway
1. Crea un proyecto → New Service → Deploy from GitHub.
2. Asegúrate de tener las variables en "Variables".
3. Railway construye con el Dockerfile y levanta Uvicorn.

## 3) Rutas principales
- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /me`
- `POST /telegram/link-code` (requiere JWT)
- `POST /telegram/link` (lo llama el bot; requiere header secreto)
- `POST /admin/users/{user_id}/plan` (admin)

## 4) Flujo "Conectar Telegram"
1) Usuario logueado llama `POST /telegram/link-code`
2) API responde: `code` y `deep_link` (t.me/CRNAssistant_bot?start=link_CODE)
3) Usuario abre link en Telegram → el bot recibe /start link_CODE
4) El bot llama a `POST /telegram/link` con:
   - Header: `X-TG-SECRET: <TELEGRAM_LINK_SECRET>`
   - Body: `{ "code": "CODE", "telegram_id": 123, "telegram_username": "..." }`
