import axios from 'axios';

// URL del backend: en Docker/Kubernetes se define con VITE_API_URL; en local usa Flask directo
export const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

// Creamos una instancia de axios con la URL de tu backend en Flask
const api = axios.create({
    baseURL: `${API_BASE}/api`,
});

// "Interceptor" que se ejecuta antes de cada petición para adjuntar el JWT automáticamente
api.interceptors.request.use(
    (config) => {
        // Buscamos el token guardado en el navegador del usuario
        const token = localStorage.getItem('token');
        if (token && !config.headers.Authorization) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Interceptor de respuesta: si el access token venció (401), se pide uno nuevo con el
// refresh token y se repite la petición original sin que el usuario lo note.
let refreshing = null;
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config;
        const refreshToken = localStorage.getItem('refresh_token');
        const isAuthCall = original?.url?.includes('/auth/login') || original?.url?.includes('/auth/refresh');

        if (error.response?.status === 401 && refreshToken && !original._retry && !isAuthCall) {
            original._retry = true;
            try {
                // Si varias peticiones fallan a la vez, todas esperan la misma renovación
                refreshing = refreshing || axios.post(`${API_BASE}/api/auth/refresh`, null, {
                    headers: { Authorization: `Bearer ${refreshToken}` },
                });
                const { data } = await refreshing;
                localStorage.setItem('token', data.access_token);
                original.headers.Authorization = `Bearer ${data.access_token}`;
                return api(original);
            } catch (refreshError) {
                localStorage.clear(); // el refresh también venció: hay que iniciar sesión de nuevo
                return Promise.reject(refreshError);
            } finally {
                refreshing = null;
            }
        }
        return Promise.reject(error);
    }
);

// Cierra la sesión en el servidor (revoca los tokens) y limpia el navegador
export const logoutSession = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    try {
        await api.post('/auth/logout');
        if (refreshToken) {
            await api.post('/auth/logout', null, { headers: { Authorization: `Bearer ${refreshToken}` } });
        }
    } catch {
        // Aunque falle la red, se borra la sesión local
    } finally {
        localStorage.clear();
    }
};

export default api;
