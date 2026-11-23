import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api/axiosConfig';

function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const response = await api.post('/auth/login', { username, password });
            localStorage.setItem('token', response.data.access_token);
            localStorage.setItem('refresh_token', response.data.refresh_token); // para renovar la sesión
            localStorage.setItem('username', response.data.username);
            localStorage.setItem('role', response.data.role);
            navigate('/tickets');
        } catch (err) {
            // 429 = el backend bloqueó temporalmente por demasiados intentos (anti fuerza bruta)
            setError(err.response?.status === 429
                ? 'Demasiados intentos fallidos. Espera un minuto e inténtalo de nuevo.'
                : 'Credenciales inválidas. Verifica tu usuario y contraseña.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-layout">
            <div className="auth-card">
                <h2>HelpDesk Pro</h2>
                <p>Ingresa tus credenciales para continuar</p>
                
                {error && <div className="error-message">{error}</div>}
                
                <form onSubmit={handleLogin}>
                    <div className="form-group">
                        <label>Usuario</label>
                        <input 
                            type="text" 
                            value={username} 
                            onChange={(e) => setUsername(e.target.value)} 
                            required 
                            placeholder="Ej: admin_soporte"
                        />
                    </div>
                    <div className="form-group">
                        <label>Contraseña</label>
                        <input 
                            type="password" 
                            value={password} 
                            onChange={(e) => setPassword(e.target.value)} 
                            required 
                            placeholder="********"
                        />
                    </div>
                    <button type="submit" className="primary-btn" disabled={loading}>
                        {loading ? 'Ingresando...' : 'Iniciar Sesión'}
                    </button>
                </form>
                
                <div className="auth-links">
                    ¿No tienes cuenta? <Link to="/register">Regístrate aquí</Link>
                </div>
            </div>
        </div>
    );
}

export default Login;