const API_URL = "http://127.0.0.1:5000";

export const checkHealth = async () => {
    try {
        const response = await fetch(`${API_URL}/health`);
        return await response.json();
    } catch (error) {
        console.error("Error conectando al backend:", error);
        return { message: "Error de conexión con el servidor IT" };
    }
};