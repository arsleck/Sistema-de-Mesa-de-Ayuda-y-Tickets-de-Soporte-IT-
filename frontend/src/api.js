import { API_BASE } from "./api/axiosConfig";

const API_URL = API_BASE;

export const checkHealth = async () => {
    try {
        const response = await fetch(`${API_URL}/health`);
        return await response.json();
    } catch (error) {
        console.error("Error conectando al backend:", error);
        return { message: "Error de conexión con el servidor IT" };
    }
};