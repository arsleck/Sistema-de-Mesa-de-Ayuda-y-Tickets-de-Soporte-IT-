import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, ArrowLeft, UserPlus } from 'lucide-react';
import api from '../api/axiosConfig';

function AdminPanel() {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleCreateAgent = async (e) => {
        e.preventDefault();
        setMessage(''); setError('');
        try {
            await api.post('/auth/admin/register', { username, email, password });
            setMessage('Técnico de soporte creado correctamente.');
            setUsername(''); setEmail(''); setPassword('');
        } catch (err) {
            setError(err.response?.data?.error || 'Error al crear el técnico.');
        }
    };

    return (
        <div className="dashboard-layout">
            <aside className="sidebar">
                <div className="sidebar-brand">
                    <ShieldCheck size={28} className="brand-icon" />
                    <h2>Panel Admin</h2>
                </div>
                <nav className="sidebar-nav">
                    <button onClick={() => navigate('/tickets')} className="nav-item">
                        <ArrowLeft size={20} /> Volver a Tickets
                    </button>
                </nav>
            </aside>

            <main className="main-content">
                <div className="header-bar">
                    <h3>Gestión de Usuarios Técnicos</h3>
                </div>
                
                <div className="content-area">
                    <div className="card form-card">
                        <div className="card-header">
                            <UserPlus size={24} color="#4f46e5" />
                            <h4>Registrar Nuevo Agente IT</h4>
                        </div>
                        {message && <div className="success-message">{message}</div>}
                        {error && <div className="error-message">{error}</div>}
                        
                        <form onSubmit={handleCreateAgent} className="ticket-form">
                            <div className="form-group">
                                <label>Usuario del Técnico</label>
                                <input type="text" value={username} onChange={(e)=>setUsername(e.target.value)} required />
                            </div>
                            <div className="form-group">
                                <label>Correo Institucional</label>
                                <input type="email" value={email} onChange={(e)=>setEmail(e.target.value)} required />
                            </div>
                            <div className="form-group">
                                <label>Contraseña Temporal</label>
                                <input type="password" value={password} onChange={(e)=>setPassword(e.target.value)} required />
                            </div>
                            <button type="submit" className="primary-btn">Crear Cuenta de Agente</button>
                        </form>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default AdminPanel;