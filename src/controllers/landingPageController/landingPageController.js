import dotenv from 'dotenv';
import { fetchWithRetry } from '../../utils/redisUtils/fetchWithCache.js';
import { redisClient } from '../../utils/redisUtils/cookiesBlackList.js';

dotenv.config();

const CACHE_KEY = 'landingPageData';
const CACHE_EXPIRATION = 36000; // 10 horas

const DATA_API_URL = `http://${process.env.DATA_API_APP_HOST}:5000`;


const getLandingPageData = async () => {
    try {

        const cachedData = await redisClient.get(CACHE_KEY);
        if (cachedData) {
            console.log('Datos obtenidos de Redis');
            return JSON.parse(cachedData);
        }
        console.log('Datos no encontrados en Redis, llamando a la API externa...');

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

        await redisClient.set(CACHE_KEY, JSON.stringify(responseData), { EX: CACHE_EXPIRATION });

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