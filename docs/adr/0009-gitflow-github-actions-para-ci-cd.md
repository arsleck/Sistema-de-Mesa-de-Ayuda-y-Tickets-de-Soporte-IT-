# ADR 0009: GitFlow + GitHub Actions para CI/CD

**Estado:** Aceptada · **Actividad del curso:** A6, A7

## Contexto
Varias personas trabajan en el repositorio y cada cambio debe probarse antes de integrarse.

## Opciones evaluadas
| Opción | Evaluación |
|---|---|
| Commits directos a main | Sin revisión ni pruebas automáticas (estado inicial del repo). |
| Jenkins / GitLab CI | Requieren servidor propio o migrar el repositorio. |
| GitHub Actions | Integrado con el repositorio, los PR y el registro de contenedores GHCR. |

## Decisión
Ramas main / develop / feature/* con PR; pipeline test → build → deploy: pytest + evidencia OWASP, lint/build, validación de k8s y Terraform, imágenes a GHCR, despliegue en kind con smoke test y despliegue a Azure con Terraform en main.

## Consecuencias
- Un PR con pruebas fallidas o un control OWASP vulnerable no pasa el pipeline.
- Las imágenes quedan versionadas por commit (SHA).
- El despliegue a Azure solo ocurre desde main y con aprobación del environment «production».
