# =====================================================================
#  Imagen del FRONTEND (React + Vite)  -> construcción en 2 etapas
#  Etapa 1: Node compila la app.   Etapa 2: Nginx sirve los archivos estáticos.
#  La imagen final NO contiene Node ni node_modules: pesa ~50 MB.
# =====================================================================

# ---------- Etapa 1: compilación ----------
FROM node:22-alpine AS build
WORKDIR /app

# Dependencias primero (capa reutilizable)
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# URL del backend vista desde el navegador. Vacía = mismo dominio (Nginx hace de proxy a /api)
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# ---------- Etapa 2: servidor web ----------
FROM nginx:1.27-alpine
# Las plantillas de /etc/nginx/templates se procesan al arrancar (envsubst)
ENV BACKEND_URL=http://backend:5000
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
