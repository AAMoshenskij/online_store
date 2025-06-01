
# Проект на тему: "Онлайн магазин"

## Участники проекта

Студент | Роль | Группа
-------------|---------------------|---
**Мошенский Андрей** | Бэкенд, Тимлид | 306
Шипилова Татьяна | Бэкенд | 306
Жаднов Михаил | Аналитик | 306
Фомин Иван | Аналитик | 309

## Использование

**Архитектуру** можно посмотреть [здесь](./ARCHITECTURE.md)

Для запуска приложения нужно:

- найти товары и оформить их, как в [примере](./data/Backpacks.csv)
- определить переменные окружения в `.env`
- запустить через `docker compose up`

Пример `.env`:

```text
# ------------------
# --- App Config ---
# ------------------

APP_NAME=FastAPI
DEBUG=false

# ------------------------
# --- Database Config ---
# ------------------------

# Main PostgreSQL DB
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432
DB_NAME=online_store

DB_DRIVER=postgresql

# Read Replica (если используется)
REPLICA_DB_HOST=db-replica
REPLICA_DB_PORT=5432

# ----------------------
# --- Redis Config ---
# ----------------------

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=  
REDIS_DB=0

# ----------------------------
# --- Elasticsearch Config ---
# ----------------------------

ES_HOST=localhost
ES_PORT=9200
ES_USER=  
ES_PASSWORD=  

# ---------------------------
# --- ClickHouse Config ---
# ---------------------------

CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_PORT_HTTP=8123
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=default

# ----------------------
# --- JWT Config ---
# ----------------------

# Use: $ openssl rand -hex 32
SECRET_KEY="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ACCESS_TOKEN_EXPIRE_MINUTES=360

# -------------------
# --- OTP Config ---
# -------------------

# Generate with: from pyotp import random_base32; print(random_base32())
OTP_SECRET_KEY="67XKYPCGFC47RJLZAEMDM6PIRJFWOT2P"
OTP_EXPIRE_SECONDS=360

# ----------------------
# --- Email Config ---
# ----------------------

USE_LOCAL_FALLBACK=true
SMTP_SERVER=mail.example.com
SMTP_PORT=587
SMTP_USERNAME=your_email@example.com
SMTP_PASSWORD=your_email_password
EMAIL_FROM=noreply@example.com

# -------------------------
# --- Monitoring Config ---
# -------------------------

PROMETHEUS_HOST=prometheus
PROMETHEUS_PORT=9090

GRAFANA_HOST=grafana
GRAFANA_PORT=3000

# ----------------------
# --- Rate Limiting ---
# ----------------------

RATE_LIMIT=100/1minute
```
