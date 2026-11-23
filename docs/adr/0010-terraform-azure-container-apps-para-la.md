# ADR 0010: Terraform + Azure Container Apps para la nube

**Estado:** Aceptada · **Actividad del curso:** A7, A8

## Contexto
El proyecto debe poder desplegarse en un proveedor de nube de forma reproducible, a bajo costo (cuenta de estudiante).

## Opciones evaluadas
| Opción | Evaluación |
|---|---|
| Crear recursos a mano en el portal | No es reproducible ni versionable. |
| Azure Kubernetes Service (AKS) | Máximo control, pero costoso y complejo para el alcance. |
| Azure App Service | Simple, pero menos natural para varios contenedores. |
| Azure Container Apps + PostgreSQL Flexible (PaaS) con Terraform | Contenedores serverless con autoescalado HTTP, TLS automático y BD gestionada. |

## Decisión
Terraform (código en inglés) que crea Resource Group, Log Analytics, PostgreSQL Flexible Server, Redis opcional, entorno de Container Apps y las apps backend (ingreso interno, 1–5 réplicas) y frontend (HTTPS público).

## Consecuencias
- `terraform plan` muestra los cambios antes de aplicarlos; `terraform destroy` elimina todo y detiene costos.
- Las mismas imágenes Docker de GHCR se ejecutan en local, Kubernetes y Azure.
- Variables sensibles marcadas como sensitive y guardadas como secretos.
