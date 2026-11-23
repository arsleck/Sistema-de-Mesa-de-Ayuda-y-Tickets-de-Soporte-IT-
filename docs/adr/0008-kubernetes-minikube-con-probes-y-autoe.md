# ADR 0008: Kubernetes (Minikube) con probes y autoescalado HPA

**Estado:** Aceptada · **Actividad del curso:** A6, A8

## Contexto
El sistema debe demostrar disponibilidad (reinicio automático, actualizaciones sin caída) y escalabilidad ante carga.

## Opciones evaluadas
| Opción | Evaluación |
|---|---|
| Solo Docker Compose | No reprograma contenedores caídos entre nodos ni escala según la carga. |
| Docker Swarm | Más simple, pero con menor adopción en la industria. |
| Kubernetes | Estándar de orquestación: Deployments, Services, probes, HPA y RBAC. |

## Decisión
Manifiestos en k8s/: Deployments con readiness/liveness probes sobre /health, RollingUpdate sin indisponibilidad, Services, PVC para PostgreSQL, HPA (2–6 réplicas al 50 % de CPU) y Prometheus con descubrimiento de pods.

## Consecuencias
- Si un pod falla, Kubernetes lo reemplaza; si la BD no responde, el pod deja de recibir tráfico.
- Con el generador de carga se observa en Grafana cómo aumentan las réplicas.
- Los mismos manifiestos se despliegan en CI sobre un clúster kind efímero.
