import { useEffect, useState } from 'react';
import { History, X } from 'lucide-react';
import api from '../api/axiosConfig';

/*
 * HISTORIAL DEL TICKET (auditoría)
 * Ventana que muestra, en orden, quién cambió qué y cuándo:
 * creación, cambios de estado, prioridad, técnico asignado y ediciones.
 * Los datos vienen de GET /api/tickets/<id>/history (tabla ticket_history).
 */

// Nombres legibles de cada campo que se audita
const FIELD_LABELS = {
    creado: 'Ticket creado',
    status: 'Estado',
    priority: 'Prioridad',
    assigned_to: 'Técnico asignado',
    title: 'Asunto',
    description: 'Detalle',
};

function TicketHistory({ ticket, onClose }) {
    const [entries, setEntries] = useState(null);
    const [error, setError] = useState('');

    useEffect(() => {
        api.get(`/tickets/${ticket.id}/history`)
            .then(res => setEntries(res.data))
            .catch(() => setError('No se pudo cargar el historial.'));
    }, [ticket.id]);

    return (
        <div className="history-overlay" onClick={onClose}>
            {/* stopPropagation: un clic dentro de la tarjeta no cierra la ventana */}
            <div className="card history-card" onClick={(e) => e.stopPropagation()}>
                <div className="card-header">
                    <History size={22} color="#4f46e5" />
                    <h4>Historial · #{ticket.id} {ticket.title}</h4>
                    <button className="icon-btn history-close" onClick={onClose}><X size={18} /></button>
                </div>

                <div className="history-body">
                    {error && <div className="error-message">{error}</div>}
                    {!entries && !error && <p className="history-empty">Cargando…</p>}
                    {entries && entries.length === 0 && <p className="history-empty">Sin cambios registrados.</p>}

                    <ul className="history-list">
                        {entries?.map(h => (
                            <li key={h.id}>
                                <span className="dot dot-en-progreso"></span>
                                <div>
                                    <strong>{FIELD_LABELS[h.field] || h.field}</strong>
                                    {h.field !== 'creado' ? (
                                        <span> · {h.old_value || 'Sin asignar'} → <b>{h.new_value || 'Sin asignar'}</b></span>
                                    ) : (
                                        <span> · {h.new_value}</span>
                                    )}
                                    <small>{h.user || 'Sistema'} · {new Date(h.created_at + 'Z').toLocaleString()}</small>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    );
}

export default TicketHistory;
