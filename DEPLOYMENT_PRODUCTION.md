# 🚀 Guía de Despliegue a Producción — LexIntellectus ERP

Esta guía detalla los pasos para desplegar **LexIntellectus** en un servidor Linux de producción (Ubuntu 22.04 / 24.04 LTS) con aislamiento de red interna, Nginx Reverse Proxy, cifrado Fernet at-rest y respaldos automatizados.

---

## 1. Requisitos Mínimos de Infraestructura

| Recurso | Mínimo Recomendado (1–5 Despachos) | Escalado (Multi-Tenant Corporativo) |
| :--- | :--- | :--- |
| **CPU** | 4 vCPU | 8+ vCPU |
| **RAM** | 8 GB RAM | 16–32 GB RAM |
| **Almacenamiento** | 80 GB NVMe SSD | 250+ GB NVMe SSD + S3 externo |
| **Sistema Operativo** | Ubuntu 24.04 LTS + Docker Engine 26+ | Ubuntu 24.04 LTS / Kubernetes |

---

## 2. Generación de Secretos Criptográficos (`.env.production`)

Antes de levantar los contenedores, cree un archivo `.env.production` en la raíz del servidor (nunca lo suba a Git) y genere claves criptográficas fuertes:

```bash
# 1. Generar JWT_SECRET_KEY (64 bytes hex)
openssl rand -hex 64

# 2. Generar ENCRYPTION_KEY (Fernet 32-byte URL-safe base64 para cifrado At-Rest)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 3. Generar contraseñas para PostgreSQL, Redis y MinIO
openssl rand -base64 32
```

### Plantilla `.env.production`
```ini
POSTGRES_USER=lexintellectus
POSTGRES_PASSWORD=<PASSWORD_FUERTE_POSTGRES>
POSTGRES_DB=lexintellectus

REDIS_PASSWORD=<PASSWORD_FUERTE_REDIS>

MINIO_ROOT_USER=lexintellectus_admin
MINIO_ROOT_PASSWORD=<PASSWORD_FUERTE_MINIO>

JWT_SECRET_KEY=<CLAVE_HEX_64_BYTES>
ENCRYPTION_KEY=<CLAVE_FERNET_BASE64>

BACKEND_CORS_ORIGINS=["https://app.tudominio.com"]
NEXT_PUBLIC_API_URL=/api/v1

GOOGLE_API_KEY=<TU_API_KEY_GEMINI>
STRIPE_SECRET_KEY=<TU_CLAVE_LIVE_O_TEST_STRIPE>
STRIPE_WEBHOOK_SECRET=<TU_SECRETO_WEBHOOK_STRIPE>

SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=<TU_API_KEY_SENDGRID>
SENDER_EMAIL=notificaciones@tudominio.com
```

---

## 3. Despliegue con Docker Compose de Producción

```bash
# 1. Validar sintaxis de configuración
docker compose -f docker-compose.prod.yml --env-file .env.production config -q

# 2. Construir imágenes y levantar servicios en segundo plano
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build

# 3. Aplicar todas las migraciones de Alembic (Sprints 1 al 9)
docker compose -f docker-compose.prod.yml --env-file .env.production exec backend alembic upgrade head

# 4. Verificar salud del sistema a través del Reverse Proxy Nginx
curl -i http://localhost/api/v1/health
```

---

## 4. Respaldos Automatizados de Base de Datos (`database/backup.sh`)

El script [database/backup.sh](file:///c:/Users/maria/LexIntellectus/database/backup.sh) genera volcados comprimidos (`pg_dump | gzip`) con retención rotativa de 7 días. Para programarlo diariamente a las 02:00 AM en el servidor:

```bash
chmod +x database/backup.sh
(crontab -l 2>/dev/null; echo "0 2 * * * cd /opt/LexIntellectus && ./database/backup.sh >> /var/log/lexintellectus_backup.log 2>&1") | crontab -
```

---

## 5. Checklist de Verificación Pre-Lanzamiento (Go-Live)

- [x] **Aislamiento de Red:** `postgres`, `redis` y `minio` están en la red interna `lexintellectus_internal` sin exponer puertos `5432`, `6379` ni `9000` a Internet en [docker-compose.prod.yml](file:///c:/Users/maria/LexIntellectus/docker-compose.prod.yml).
- [x] **Reverse Proxy & Cabeceras de Seguridad:** [nginx/nginx.conf](file:///c:/Users/maria/LexIntellectus/nginx/nginx.conf) aplica `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, compresión Gzip y `client_max_body_size 25M`.
- [x] **Rate Limiting en Doble Capa:** Zona `auth_limit` en Nginx + `FastAPILimiter` respaldado por Redis en `/api/v1/auth/login` y rate limiting por clave en `/api/v1/public/*`.
- [x] **Seguridad de Credenciales:** 2FA TOTP habilitado en UI, contraseñas con Bcrypt, `ApiKey` almacenadas con SHA-256 y campos PII cifrados at-rest con Fernet (`EncryptedString`).
- [x] **CI/CD Automatizado:** Pipeline [ci-cd.yml](file:///c:/Users/maria/LexIntellectus/.github/workflows/ci-cd.yml) ejecutando las 53 pruebas automatizadas (`pytest`), compilación de Next.js 14 y validación de `docker-compose.prod.yml` en cada `push` o `pull_request`.
