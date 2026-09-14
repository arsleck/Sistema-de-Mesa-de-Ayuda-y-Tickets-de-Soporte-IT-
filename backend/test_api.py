import requests

# 1. Hacer Login para obtener el token automáticamente
print("Iniciando sesión...")
login_url = 'http://127.0.0.1:5000/api/auth/login'
credenciales = {
    "username": "admin_soporte", 
    "password": "super_secreta_123"
}

respuesta_login = requests.post(login_url, json=credenciales)

if respuesta_login.status_code == 200:
    token = respuesta_login.json().get('access_token')
    print(f"✅ Login exitoso. Token obtenido.\n")
    
    # 2. Usar el token para crear un Ticket
    print("Intentando crear un ticket...")
    tickets_url = 'http://127.0.0.1:5000/api/tickets/'
    
    # Aquí es donde inyectamos la cabecera limpia, sin errores de Postman
    cabeceras = {
        "Authorization": f"Bearer {token}"
    }
    datos_ticket = {
        "title": "La impresora del piso 3 no enciende",
        "description": "Se revisaron los cables pero sigue sin encender, arroja un error E02.",
        "priority": "Alta"
    }
    
    respuesta_ticket = requests.post(tickets_url, json=datos_ticket, headers=cabeceras)
    
    print(f"Código de estado: {respuesta_ticket.status_code}")
    print(f"Respuesta del servidor: {respuesta_ticket.json()}")

else:
    print(f"❌ Error en el login: {respuesta_login.json()}")