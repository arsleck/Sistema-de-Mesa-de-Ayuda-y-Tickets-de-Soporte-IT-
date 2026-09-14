import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, LogOut, PlusCircle, Search, Ticket as TicketIcon, Trash2, UserCircle, Briefcase } from 'lucide-react';
import api from '../api/axiosConfig';

function Tickets() {
    const [tickets, setTickets] = useState([]);
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [priority, setPriority] = useState('Media');
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('Todos');
    const [agents, setAgents] = useState([]);

    const navigate = useNavigate();
    const currentUsername = localStorage.getItem('username') || 'Usuario';
    const currentUserRole = localStorage.getItem('role') || 'employee';

    useEffect(() => {
        fetchTickets();
        if (currentUserRole !== 'employee') {
            fetchAgents();
        }
    }, [currentUserRole]);

    const fetchTickets = async () => {
        try {
            const response = await api.get('/tickets');
            setTickets(response.data);
        } catch (error) {
            if (error.response?.status === 401) handleLogout();
        }
    };

    const fetchAgents = async () => {
        try {
            const response = await api.get('/auth/agents');
            setAgents(response.data);
        } catch (error) {
            console.error("Error al cargar agentes");
        }
    };

    const handleCreateTicket = async (e) => {
        e.preventDefault();
        try {
            await api.post('/tickets', { title, description, priority });
            setTitle(''); setDescription(''); setPriority('Media');
            fetchTickets();
        } catch (error) {
            alert("Error al crear el ticket.");
        }
    };

    const handleUpdateStatus = async (id, newStatus) => {
        try {
            await api.put(`/tickets/${id}`, { status: newStatus });
            fetchTickets();
        } catch (error) {
            alert("Error al actualizar estado.");
        }
    };

    const handleDeleteTicket = async (id) => {
        if (window.confirm("¿Eliminar este ticket de forma permanente?")) {
            try {
                await api.delete(`/tickets/${id}`);
                fetchTickets(); 
            } catch (error) {
                alert("Error al eliminar.");
            }
        }
    };

    const handleLogout = () => {
        localStorage.clear();
        navigate('/login');
    };

    const filteredTickets = tickets.filter(ticket => {
        const matchesSearch = ticket.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                              ticket.description.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = filterStatus === 'Todos' || ticket.status === filterStatus;
        return matchesSearch && matchesStatus;
    });

    return (
        <div className="dashboard-layout">
            {/* BARRA LATERAL (SIDEBAR) */}
            <aside className="sidebar">
                <div className="sidebar-brand">
                    <Briefcase size={28} className="brand-icon" />
                    <h2>HelpDesk Pro</h2>
                </div>
                
                <div className="sidebar-user">
                    <UserCircle size={36} color="#94a3b8" />
                    <div>
                        <span className="user-name">{currentUsername}</span>
                        <span className="user-role">{currentUserRole === 'admin' ? 'Administrador' : currentUserRole === 'agent' ? 'Técnico IT' : 'Usuario'}</span>
                    </div>
                </div>

                <nav className="sidebar-nav">
                    <button className="nav-item active">
                        <LayoutDashboard size={20} /> Dashboard
                    </button>
                    {currentUserRole === 'admin' && (
                        <button onClick={() => navigate('/admin')} className="nav-item">
                            <Users size={20} /> Gestión de Agentes
                        </button>
                    )}
                    <button onClick={handleLogout} className="nav-item logout">
                        <LogOut size={20} /> Cerrar Sesión
                    </button>
                </nav>
            </aside>

            {/* CONTENIDO PRINCIPAL */}
            <main className="main-content">
                <div className="header-bar">
                    <h3>Resumen de Operaciones</h3>
                    <div className="filters-bar">
                        <div className="search-wrapper">
                            <Search size={18} className="search-icon" />
                            <input 
                                type="text" 
                                placeholder="Buscar ticket..." 
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="search-input"
                            />
                        </div>
                        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="filter-select">
                            <option value="Todos">Todos los estados</option>
                            <option value="Abierto">Abiertos</option>
                            <option value="En Progreso">En Progreso</option>
                            <option value="Resuelto">Resueltos</option>
                        </select>
                    </div>
                </div>

                <div className="content-area">
                    {/* Panel Izquierdo: Crear Ticket */}
                    <div className="creation-section">
                        <div className="card form-card">
                            <div className="card-header">
                                <PlusCircle size={22} color="#4f46e5" />
                                <h4>Generar Incidencia</h4>
                            </div>
                            <form onSubmit={handleCreateTicket} className="ticket-form">
                                <div className="form-group">
                                    <label>Asunto</label>
                                    <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required />
                                </div>
                                <div className="form-group">
                                    <label>Detalle del problema</label>
                                    <textarea value={description} onChange={(e) => setDescription(e.target.value)} required rows="4"></textarea>
                                </div>
                                <div className="form-group">
                                    <label>Prioridad</label>
                                    <select value={priority} onChange={(e) => setPriority(e.target.value)}>
                                        <option value="Baja">Baja</option>
                                        <option value="Media">Media</option>
                                        <option value="Alta">Alta</option>
                                    </select>
                                </div>
                                <button type="submit" className="primary-btn">Registrar Ticket</button>
                            </form>
                        </div>
                    </div>

                    {/* Panel Derecho: Lista de Tickets */}
                    <div className="list-section">
                        {/* MÉTRICAS (Solo visibles para staff) */}
                        {currentUserRole !== 'employee' && (
                            <div className="metrics-grid">
                                <div className="metric-box">
                                    <h5>Total</h5>
                                    <span>{filteredTickets.length}</span>
                                </div>
                                <div className="metric-box open">
                                    <h5>Abiertos</h5>
                                    <span>{filteredTickets.filter(t => t.status === 'Abierto').length}</span>
                                </div>
                                <div className="metric-box solved">
                                    <h5>Resueltos</h5>
                                    <span>{filteredTickets.filter(t => t.status === 'Resuelto').length}</span>
                                </div>
                            </div>
                        )}

                        <div className="tickets-grid">
                            {filteredTickets.length === 0 ? (
                                <div className="empty-state">
                                    <TicketIcon size={48} color="#cbd5e1" />
                                    <p>No hay tickets para mostrar.</p>
                                </div>
                            ) : (
                                filteredTickets.map(ticket => (
                                    <div key={ticket.id} className="ticket-card">
                                        <div className="ticket-header">
                                            <h4>{ticket.title}</h4>
                                            <div className="header-actions">
                                                <span className={`badge badge-${ticket.priority.toLowerCase()}`}>
                                                    {ticket.priority}
                                                </span>
                                                {(currentUserRole === 'admin' || currentUserRole === 'agent') && (
                                                    <button onClick={() => handleDeleteTicket(ticket.id)} className="icon-btn delete">
                                                        <Trash2 size={18} />
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                        
                                        <div className="ticket-meta">
                                            <UserCircle size={14} /> 
                                            <span>Reportado por: {ticket.creator_username || 'Usuario'}</span>
                                        </div>

                                        <p className="ticket-desc">{ticket.description}</p>
                                        
                                        <div className="ticket-footer">
                                            <div className="status-control">
                                                <span className={`dot dot-${ticket.status.toLowerCase().replace(' ', '-')}`}></span>
                                                {currentUserRole !== 'employee' ? (
                                                    <select value={ticket.status} onChange={(e) => handleUpdateStatus(ticket.id, e.target.value)} className="clean-select">
                                                        <option value="Abierto">Abierto</option>
                                                        <option value="En Progreso">En Progreso</option>
                                                        <option value="Resuelto">Resuelto</option>
                                                    </select>
                                                ) : (
                                                    <span className="status-text">{ticket.status}</span>
                                                )}
                                            </div>
                                            
                                            {currentUserRole !== 'employee' && (
                                                <div className="assign-control">
                                                    <select 
                                                        value={ticket.assigned_to_id || ''} 
                                                        onChange={async (e) => {
                                                            try {
                                                                await api.put(`/tickets/${ticket.id}`, { assigned_to_id: e.target.value || null });
                                                                fetchTickets();
                                                            } catch (error) { alert("Error"); }
                                                        }}
                                                        className="clean-select assign"
                                                    >
                                                        <option value="">Sin asignar</option>
                                                        {agents.map(a => <option key={a.id} value={a.id}>{a.username}</option>)}
                                                    </select>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default Tickets;