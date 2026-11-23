import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
    ClipboardCheck, ArrowLeft, Play, CircleCheck, CircleX, LoaderCircle, Circle,
    ExternalLink, ShieldAlert, ChevronDown, ChevronUp
} from 'lucide-react';
import { API_BASE } from '../api/axiosConfig';

/*
 * CENTRO DE VERIFICACIÓN
 * Página para la sustentación: ejecuta, en orden y contra el backend real, una
 * prueba por cada requisito del curso y muestra el resultado de forma visual
 * (verde = cumple, rojo = falla), con el código HTTP, el tiempo y la evidencia.
 */

// Petición "cruda" (sin el interceptor) para poder observar exactamente qué responde el backend
const call = async (method, path, { data, token, headers = {} } = {}) => {
    const start = performance.now();
    const res = await axios({
        method, url: `${API_BASE}${path}`, data,
        headers: { ...headers, ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        validateStatus: () => true, // no lanzar error con 4xx/5xx: queremos verlos
    });
    return { ...res, ms: Math.round(performance.now() - start) };
};

// Decodifica la parte central del JWT (payload) para mostrar su contenido
const decodeJwt = (token) => {
    try {
        const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
        return JSON.parse(atob(payload));
    } catch {
        return null;
    }
};

const XSS_PAYLOAD = '<script>alert("XSS")</script><img src=x onerror=alert(1)>Prueba XSS verificación';

// Lista de verificaciones: cada una indica qué requisito del curso demuestra
const STEPS = [
    {
        id: 'health', tag: 'A8 · Monitoreo', title: 'Backend y base de datos activos',
        explains: 'El endpoint /health consulta la base de datos; lo usan Docker y Kubernetes para saber si el servicio está sano.',
        run: async () => {
            const r = await call('get', '/health');
            return { ok: r.status === 200 && r.data.database === 'ok', code: r.status, ms: r.ms,
                detail: `API: ${r.data.status} · Base de datos: ${r.data.database}`, evidence: r.data };
        },
    },
    {
        id: 'openapi', tag: 'A1 · A4 · OpenAPI', title: 'Documentación OpenAPI 3.0 publicada',
        explains: 'La especificación describe todos los endpoints y se puede probar en Swagger UI.',
        link: `${API_BASE}/api/docs`,
        run: async () => {
            const r = await call('get', '/api/openapi.yaml');
            const paths = (String(r.data).match(/^ {2}\/[^\s:]+:/gm) || []).map(p => p.trim().replace(':', ''));
            return { ok: r.status === 200 && String(r.data).includes('openapi: 3.0'), code: r.status, ms: r.ms,
                detail: `${paths.length} rutas documentadas`, evidence: paths };
        },
    },
    {
        id: 'jwt', tag: 'A3 · JWT', title: 'Sesión autenticada con JWT',
        explains: 'El token viaja en el header Authorization. Su contenido (payload) indica el usuario, el rol y cuándo expira.',
        run: async ({ token }) => {
            const r = await call('get', '/api/auth/me', { token });
            const p = decodeJwt(token) || {};
            const exp = p.exp ? new Date(p.exp * 1000).toLocaleTimeString() : '—';
            return { ok: r.status === 200, code: r.status, ms: r.ms,
                detail: `Usuario: ${r.data.username} · Rol: ${p.role} · Expira: ${exp}`,
                evidence: { payload_del_token: p, respuesta: r.data } };
        },
    },
    {
        id: 'refresh', tag: 'A3 · OAuth 2.1', title: 'Renovación con refresh token',
        explains: 'Con el refresh token se obtiene un access token nuevo sin volver a pedir la contraseña.',
        run: async ({ refresh }) => {
            const r = await call('post', '/api/auth/refresh', { token: refresh });
            if (r.status === 200) localStorage.setItem('token', r.data.access_token);
            return { ok: r.status === 200 && !!r.data.access_token, code: r.status, ms: r.ms,
                detail: r.status === 200 ? 'Nuevo access token emitido y guardado' : 'No se pudo renovar',
                evidence: { access_token: `${String(r.data.access_token).slice(0, 40)}…` } };
        },
    },
    {
        id: 'noauth', tag: 'A3 · Seguridad', title: 'Petición sin token es rechazada',
        explains: 'Sin el header Authorization el backend responde 401: no hay datos sin autenticación.',
        run: async () => {
            const r = await call('get', '/api/tickets');
            return { ok: r.status === 401, code: r.status, ms: r.ms, detail: 'Esperado: 401 Unauthorized', evidence: r.data };
        },
    },
    {
        id: 'rbac', tag: 'A3 · RBAC', title: 'Control de acceso por rol',
        explains: 'El listado de usuarios es solo para admin. Un técnico debe recibir 403 Forbidden.',
        run: async ({ token, role }) => {
            const r = await call('get', '/api/auth/users', { token: localStorage.getItem('token') || token });
            const expected = role === 'admin' ? 200 : 403;
            return { ok: r.status === expected, code: r.status, ms: r.ms,
                detail: `Rol ${role}: esperado ${expected}, recibido ${r.status}`,
                evidence: Array.isArray(r.data) ? r.data.map(u => `${u.username} (${u.role})`) : r.data };
        },
    },
    {
        id: 'crud', tag: 'A1 · A2 · CRUD + ORM', title: 'Ciclo CRUD completo persistido en la BD',
        explains: 'Crea, consulta, actualiza y elimina un ticket de prueba: React → API → SQLAlchemy → base de datos.',
        run: async () => {
            const token = localStorage.getItem('token');
            const log = [];
            const c = await call('post', '/api/tickets', { token, data: { title: 'Ticket de verificación', description: 'Creado por el Centro de verificación', priority: 'Baja' } });
            log.push(`POST   → ${c.status}`);
            const id = c.data.ticket?.id;
            const g = await call('get', `/api/tickets/${id}`, { token });
            log.push(`GET    → ${g.status}`);
            const u = await call('put', `/api/tickets/${id}`, { token, data: { status: 'En Progreso', priority: 'Alta' } });
            log.push(`PUT    → ${u.status} (estado: ${u.data.ticket?.status}, prioridad: ${u.data.ticket?.priority})`);
            const d = await call('delete', `/api/tickets/${id}`, { token });
            log.push(`DELETE → ${d.status}`);
            const gone = await call('get', `/api/tickets/${id}`, { token });
            log.push(`GET    → ${gone.status} (ya no existe)`);
            const ok = c.status === 201 && g.status === 200 && u.status === 200 && d.status === 200 && gone.status === 404;
            return { ok, code: c.status, ms: c.ms + g.ms + u.ms + d.ms + gone.ms, detail: `Ticket #${id}: crear · leer · actualizar · eliminar`, evidence: log };
        },
    },
    {
        id: 'xss', tag: 'A3 · OWASP XSS', title: 'Código malicioso (XSS) eliminado',
        explains: 'Se envía un ticket con <script> y <img onerror>. El backend guarda solo el texto limpio.',
        run: async () => {
            const token = localStorage.getItem('token');
            const r = await call('post', '/api/tickets', { token, data: { title: XSS_PAYLOAD, description: XSS_PAYLOAD } });
            const saved = r.data.ticket?.title || '';
            if (r.data.ticket) await call('delete', `/api/tickets/${r.data.ticket.id}`, { token });
            return { ok: r.status === 201 && !saved.includes('<'), code: r.status, ms: r.ms,
                detail: `Guardado: "${saved}"`, evidence: { enviado: XSS_PAYLOAD, guardado: saved } };
        },
    },
    {
        id: 'sqli', tag: 'A3 · OWASP SQLi', title: 'Inyección SQL neutralizada',
        explains: "Se intenta entrar con usuario ' OR '1'='1' -- y buscar con ' OR 1=1 --. El ORM los trata como texto.",
        run: async () => {
            const login = await call('post', '/api/auth/login', { data: { username: "' OR '1'='1' --", password: "' OR '1'='1" } });
            const search = await call('get', `/api/tickets?q=${encodeURIComponent("' OR 1=1 --")}`, { token: localStorage.getItem('token') });
            const ok = login.status === 401 && search.status === 200 && search.data.length === 0;
            return { ok, code: login.status, ms: login.ms + search.ms,
                detail: `Login malicioso → ${login.status} · Búsqueda maliciosa → ${search.data.length} resultados`,
                evidence: { login: login.data, resultados_busqueda: search.data } };
        },
    },
    {
        id: 'headers', tag: 'A3 · CSRF · Cabeceras', title: 'Cabeceras de seguridad y CORS',
        explains: 'El navegador recibe políticas anti-XSS y anti-clickjacking. CORS solo autoriza al frontend propio.',
        run: async () => {
            const r = await call('get', '/health');
            const names = ['content-security-policy', 'x-frame-options', 'x-content-type-options', 'referrer-policy'];
            const found = Object.fromEntries(names.map(h => [h, r.headers[h] || 'NO PRESENTE']));
            const ok = names.every(h => r.headers[h]);
            return { ok, code: r.status, ms: r.ms, detail: `${names.filter(h => r.headers[h]).length}/${names.length} cabeceras presentes`, evidence: found };
        },
    },
];

function StatusIcon({ state }) {
    if (state === 'running') return <LoaderCircle size={22} className="verify-spin" color="#4f46e5" />;
    if (state === 'ok') return <CircleCheck size={22} color="#22c55e" />;
    if (state === 'fail') return <CircleX size={22} color="#ef4444" />;
    return <Circle size={22} color="#cbd5e1" />;
}

function Verificacion() {
    const navigate = useNavigate();
    const role = localStorage.getItem('role') || 'employee';
    const [results, setResults] = useState({});     // resultado de cada paso por id
    const [running, setRunning] = useState(false);
    const [open, setOpen] = useState({});           // pasos con la evidencia desplegada
    const [brute, setBrute] = useState(null);       // resultado de la prueba de fuerza bruta

    const runAll = async () => {
        setRunning(true);
        setResults({});
        const ctx = { token: localStorage.getItem('token'), refresh: localStorage.getItem('refresh_token'), role };
        // Se ejecutan en secuencia (uno tras otro) para que la demostración sea fácil de seguir
        for (const step of STEPS) {
            setResults(prev => ({ ...prev, [step.id]: { state: 'running' } }));
            await new Promise(r => setTimeout(r, 350));
            try {
                const res = await step.run(ctx);
                setResults(prev => ({ ...prev, [step.id]: { ...res, state: res.ok ? 'ok' : 'fail' } }));
            } catch (e) {
                setResults(prev => ({ ...prev, [step.id]: { state: 'fail', detail: e.message } }));
            }
        }
        setRunning(false);
    };

    // Prueba aparte porque bloquea el login desde esta IP durante 1 minuto
    const runBruteForce = async () => {
        if (!window.confirm('Esta prueba bloqueará el inicio de sesión desde este equipo durante 1 minuto. ¿Continuar?')) return;
        setBrute({ state: 'running' });
        const codes = [];
        for (let i = 0; i < 7; i++) {
            const r = await call('post', '/api/auth/login', { data: { username: 'atacante_demo', password: `clave_${i}` } });
            codes.push(r.status);
            setBrute({ state: 'running', codes: [...codes] });
        }
        setBrute({ state: codes.includes(429) ? 'ok' : 'fail', codes });
    };

    const done = Object.values(results).filter(r => r.state === 'ok' || r.state === 'fail');
    const passed = done.filter(r => r.state === 'ok').length;
    const progress = Math.round((done.length / STEPS.length) * 100);

    return (
        <div className="dashboard-layout">
            <aside className="sidebar">
                <div className="sidebar-brand">
                    <ClipboardCheck size={28} className="brand-icon" />
                    <h2>Verificación</h2>
                </div>
                <nav className="sidebar-nav">
                    <button onClick={() => navigate('/tickets')} className="nav-item">
                        <ArrowLeft size={20} /> Volver a Tickets
                    </button>
                    <a href={`${API_BASE}/api/docs`} target="_blank" rel="noreferrer" className="nav-item">
                        <ExternalLink size={20} /> Swagger UI
                    </a>
                </nav>
            </aside>

            <main className="main-content">
                <div className="header-bar">
                    <h3>Centro de Verificación de Requisitos</h3>
                    <button onClick={runAll} disabled={running} className="primary-btn verify-run-btn">
                        <Play size={18} /> {running ? 'Ejecutando…' : 'Ejecutar verificación'}
                    </button>
                </div>

                <div className="verify-area">
                    <div className="metrics-grid">
                        <div className="metric-box"><h5>Pruebas</h5><span>{STEPS.length}</span></div>
                        <div className="metric-box solved"><h5>Aprobadas</h5><span>{passed}</span></div>
                        <div className="metric-box failed"><h5>Fallidas</h5><span>{done.length - passed}</span></div>
                    </div>

                    <div className="verify-progress"><div style={{ width: `${progress}%` }} /></div>

                    <div className="verify-list">
                        {STEPS.map((step, i) => {
                            const r = results[step.id] || { state: 'pending' };
                            return (
                                <div key={step.id} className={`card verify-step ${r.state}`}>
                                    <div className="verify-step-main">
                                        <span className="verify-num">{i + 1}</span>
                                        <StatusIcon state={r.state} />
                                        <div className="verify-text">
                                            <div className="verify-title">
                                                <h4>{step.title}</h4>
                                                <span className="badge verify-tag">{step.tag}</span>
                                            </div>
                                            <p>{step.explains}</p>
                                            {r.detail && <p className="verify-detail">{r.detail}</p>}
                                        </div>
                                        <div className="verify-meta">
                                            {r.code && <span className={`verify-code ${r.state}`}>HTTP {r.code}</span>}
                                            {r.ms !== undefined && <span className="verify-ms">{r.ms} ms</span>}
                                            {step.link && <a href={step.link} target="_blank" rel="noreferrer" className="icon-btn"><ExternalLink size={16} /></a>}
                                            {r.evidence && (
                                                <button className="icon-btn" onClick={() => setOpen(o => ({ ...o, [step.id]: !o[step.id] }))}>
                                                    {open[step.id] ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                    {open[step.id] && r.evidence && (
                                        <pre className="verify-evidence">{JSON.stringify(r.evidence, null, 2)}</pre>
                                    )}
                                </div>
                            );
                        })}

                        {/* Prueba opcional de fuerza bruta (OWASP A07) */}
                        <div className={`card verify-step ${brute?.state || 'pending'}`}>
                            <div className="verify-step-main">
                                <span className="verify-num">{STEPS.length + 1}</span>
                                <StatusIcon state={brute?.state} />
                                <div className="verify-text">
                                    <div className="verify-title">
                                        <h4>Bloqueo de fuerza bruta (opcional)</h4>
                                        <span className="badge verify-tag">A3 · OWASP A07</span>
                                    </div>
                                    <p>Se envían 7 intentos de login fallidos: a partir del sexto el backend responde 429 Too Many Requests.</p>
                                    {brute?.codes && <p className="verify-detail">Respuestas: {brute.codes.join(' · ')}</p>}
                                </div>
                                <div className="verify-meta">
                                    <button onClick={runBruteForce} disabled={brute?.state === 'running'} className="clean-select verify-brute-btn">
                                        <ShieldAlert size={16} /> Ejecutar
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default Verificacion;
