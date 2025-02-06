import axios from 'axios';

export const fetchWithRetry = async (url, retries = 3, delay = 1000) => {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await axios.get(url, {
                timeout: 5000, // 5 segundos de timeout
                headers: {
                    'Connection': 'close' // Forzar el cierre de la conexión después de cada petición
                }
            });
            return response.data;
        } catch (error) {
            if (i === retries - 1) throw error; // Si es el último intento, propagar el error
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
};
