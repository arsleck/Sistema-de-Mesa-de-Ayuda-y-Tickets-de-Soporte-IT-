"""
Documentación interactiva de la API (Swagger UI + OpenAPI 3.0).

- GET /api/openapi.yaml -> la especificación OpenAPI (archivo docs/openapi.yaml)
- GET /api/docs         -> Swagger UI: permite leer y PROBAR cada endpoint desde el navegador
"""
import os

from flask import Blueprint, Response, abort

docs_bp = Blueprint('docs', __name__)

# Busca la especificación en la carpeta docs/ del repositorio (o donde indique OPENAPI_PATH)
_BASE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.getenv('OPENAPI_PATH', ''),
    os.path.join(_BASE, '..', '..', '..', 'docs', 'openapi.yaml'),  # ejecución local
    os.path.join(_BASE, '..', '..', 'docs', 'openapi.yaml'),        # dentro del contenedor Docker
]

SWAGGER_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>HelpDesk Pro · API Docs</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({ url: '/api/openapi.yaml', dom_id: '#swagger-ui', persistAuthorization: true });
  </script>
</body>
</html>"""


@docs_bp.route('/api/openapi.yaml', methods=['GET'])
def openapi_spec():
    for path in _CANDIDATES:
        if path and os.path.isfile(path):
            with open(path, encoding='utf-8') as f:
                return Response(f.read(), mimetype='application/yaml')
    abort(404)


@docs_bp.route('/api/docs', methods=['GET'])
def swagger_ui():
    return Response(SWAGGER_HTML, mimetype='text/html')
