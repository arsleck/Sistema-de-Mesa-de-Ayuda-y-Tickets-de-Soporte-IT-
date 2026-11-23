"""Punto de entrada para desarrollo local: python run.py"""
import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    # El modo debug solo se activa si FLASK_DEBUG=1 (nunca fijo en el código)
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, host=os.getenv('FLASK_HOST', '127.0.0.1'), port=int(os.getenv('PORT', 5000)))
