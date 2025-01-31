import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const DATA_API_URL = `http://${process.env.DATA_API_APP_HOST}:5000`;

// Función de utilidad para hacer llamadas con reintentos
const fetchWithRetry = async (url, retries = 3, delay = 1000) => {
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
            console.log(`Intento ${i + 1} fallido para ${url}, reintentando...`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
};

const getLandingPageData = async () => {
    try {
        console.log('Fetching landing page data from DATA API');
        
        // Hacer las llamadas de forma secuencial para evitar sobrecarga
        const usersAnalysis = await fetchWithRetry(`${DATA_API_URL}/analyze_users`);
        
        const monthlyAverage = await fetchWithRetry(`${DATA_API_URL}/analyze_monthly_average_simple`);
        
        const monthlySavings = await fetchWithRetry(`${DATA_API_URL}/analyze_monthly_savings`);
        
        const totalOperations = await fetchWithRetry(`${DATA_API_URL}/analyze_total_simple`);
        
        const cashFlow = await fetchWithRetry(`${DATA_API_URL}/analyze_cash_flow`);

        // Construir y retornar el objeto de respuesta consolidado
        const responseData = {
            userAnalysis: usersAnalysis,
            monthlyAverageSpending: monthlyAverage,
            monthlySavingsAverage: monthlySavings,
            totalOperationsData: totalOperations,
            cashFlowAnalysis: cashFlow
        };

        return responseData;

    } catch (error) {
        if (error.response) {
            console.error('Response error data:', error.response.data);
            console.error('Response error status:', error.response.status);
        }
        throw {
            status: error.response?.status || 500,
            message: error.response?.data?.error || 'Error al obtener los datos de la landing page',
            details: error.message // Incluir más detalles del error para debugging
        };
    }
};

export const landingPageController = {
    getLandingPageData
};

export default landingPageController;