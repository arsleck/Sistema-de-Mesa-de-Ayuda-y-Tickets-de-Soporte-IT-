# =====================================================================
#  Imagen del BACKEND (Flask + Gunicorn)
#  Se construye desde la RAÍZ del repo para poder copiar docs/openapi.yaml:
#      docker build -f backend/Dockerfile -t helpdesk-backend .
# =====================================================================

# Imagen base liviana de Python
FROM python:3.12-slim

# Variables para que Python no genere .pyc y muestre los logs al instante
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 1) Primero solo las dependencias: Docker reutiliza esta capa si el código cambia
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# 2) Luego el código de la aplicación y la especificación OpenAPI (para Swagger UI)
COPY backend/ .
COPY docs/openapi.yaml /app/docs/openapi.yaml

# Seguridad: el contenedor NO corre como root
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 5000

# Docker revisa cada 30 s que la API responda (/health también verifica la BD)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/health').status==200 else 1)"

# Gunicorn = servidor de producción (en lugar del servidor de desarrollo de Flask)
# 1 proceso con 4 hilos; para escalar se agregan más contenedores/pods (réplicas)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--access-logfile", "-", "run:app"]
