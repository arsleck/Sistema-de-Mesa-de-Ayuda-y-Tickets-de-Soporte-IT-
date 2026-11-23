# Registro de decisiones de arquitectura (ADR)

Cada documento explica **qué** se decidió, **por qué** y **qué alternativas se descartaron**. Formato: *Contexto → Opciones evaluadas → Decisión → Consecuencias*.

| ADR | Decisión | Actividad |
|---|---|---|
| [0001](0001-arquitectura-desacoplada.md) | Arquitectura desacoplada: SPA en React + API REST en Flask | A1, A2 |
| [0002](0002-postgresql-con-sqlalchemy-orm.md) | PostgreSQL con SQLAlchemy ORM | A2, A3 |
| [0003](0003-jwt-con-access-refresh-token-en-el-hea.md) | JWT con access + refresh token en el header Authorization | A3 |
| [0004](0004-autorizacion-rbac-aplicada-en-el-backend.md) | Autorización RBAC aplicada en el backend | A3 |
| [0005](0005-contenedores-docker.md) | Contenedores Docker: Gunicorn para la API y Nginx para el frontend | A5 |
| [0006](0006-observabilidad-con-prometheus-grafana.md) | Observabilidad con Prometheus + Grafana y métricas de negocio | A8 |
| [0007](0007-redis-para-compartir-el-limite-de-intent.md) | Redis para compartir el límite de intentos entre réplicas | A3, A6, A8 |
| [0008](0008-kubernetes-minikube-con-probes-y-autoe.md) | Kubernetes (Minikube) con probes y autoescalado HPA | A6, A8 |
| [0009](0009-gitflow-github-actions-para-ci-cd.md) | GitFlow + GitHub Actions para CI/CD | A6, A7 |
| [0010](0010-terraform-azure-container-apps-para-la.md) | Terraform + Azure Container Apps para la nube | A7, A8 |
