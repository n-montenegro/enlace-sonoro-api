# =====================================================================================
# Dockerfile MULTI-STAGE de Enlace Sonoro (Guía 8)
#
#   Etapa 1 "builder": crea un entorno virtual e instala las dependencias de producción.
#   Etapa 2 "runtime": parte de una imagen limpia y copia SOLO el entorno virtual y el código.
#   pip, su caché y los archivos temporales de la instalación se quedan en la etapa 1.
#
# Construir:  docker build -t enlace-sonoro-api .
# Ejecutar:   docker compose up --build      (API + PostgreSQL, ver docker-compose.yml)
# =====================================================================================

# ---------- Etapa 1: builder ----------
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN python -m venv /opt/venv
COPY requirements-prod.txt /tmp/requirements-prod.txt
# Mismas reglas del CI: versiones fijas con hash SHA-256 y solo paquetes binarios (cadena de suministro)
RUN /opt/venv/bin/pip install --only-binary :all: --require-hashes -r /tmp/requirements-prod.txt


# ---------- Etapa 2: runtime ----------
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="Enlace Sonoro API" \
      org.opencontainers.image.source="https://github.com/n-montenegro/enlace-sonoro-api" \
      org.opencontainers.image.authors="Nicolas Montenegro Gonzalez, Jhorman David Pardo Villamil"

# El pipeline pone aquí el commit (git sha); /health lo muestra para saber qué versión está desplegada
ARG APP_VERSION=dev

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000 \
    APP_VERSION=${APP_VERSION} \
    DB_PATH=/app/data/enlace_sonoro.db

# Usuario SIN privilegios: si alguien encontrara una falla en la app, no sería root dentro del contenedor
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
# El código queda como propiedad de root: el usuario de la app puede leerlo pero NO modificarlo
COPY app ./app
# Únicas carpetas donde la app escribe: registro de llamadas a la IA, copias de los datos abiertos
# y la base SQLite cuando no hay DATABASE_URL (DB_PATH). /app es de root y appuser no puede escribir ahí.
RUN mkdir logs data && chown appuser:appuser logs data

USER appuser

EXPOSE 8000

# Docker revisa cada 30 s que la API y la base de datos respondan (GET /health)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ['PORT'], timeout=4)"]

# Render asigna el puerto en la variable PORT; en local es 8000.
# --proxy-headers: detrás del proxy de Render se usa la IP real del cliente (importante para el rate limiting)
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port \"$PORT\" --proxy-headers"]
