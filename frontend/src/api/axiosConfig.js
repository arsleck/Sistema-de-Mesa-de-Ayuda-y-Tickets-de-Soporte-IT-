import axios from 'axios';

// Creamos una instancia de axios con la URL de tu backend en Flask
const api = axios.create({
    baseURL: 'http://127.0.0.1:5000/api',
});

// "Interceptor" que se ejecuta antes de cada petición para adjuntar el JWT automáticamente
api.interceptors.request.use(
    (config) => {
        // Buscamos el token guardado en el navegador del usuario
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default api;