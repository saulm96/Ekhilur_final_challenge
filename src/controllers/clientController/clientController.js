import dotenv from 'dotenv';
import { redisClient } from '../../utils/redisUtils/cookiesBlackList.js';
import { fetchWithRetry } from '../../utils/redisUtils/fetchWithCache.js';

dotenv.config();

const CACHE_KEY = 'clients';
const CACHE_EXPIRATION = 36000; // 10 horas 

const DATA_API_URL = `http://${process.env.DATA_API_APP_HOST}:5000`;



const getClientPageData = async () => {
    try {
        // Intentar obtener la respuesta completa de Redis
        const cachedData = await redisClient.get(CACHE_KEY);

        if (cachedData) {
            // Si los datos están en caché, devolverlos
            console.log('Datos obtenidos de Redis');
            return JSON.parse(cachedData);
        }

        // Si no están en caché, obtener los datos de la API externa
        console.log('Datos no encontrados en Redis, llamando a la API externa...');

        // Usar las rutas correctas que existen en la API Flask
        const usuariosPorEdad = await fetchWithRetry(`${DATA_API_URL}/cantidad-usuarios-grupo-edad`);
        const evolucionAltas = await fetchWithRetry(`${DATA_API_URL}/evolucion-altas-mes`);
        const porcentajePagos = await fetchWithRetry(`${DATA_API_URL}/porcentaje-pagos-qr-app`);
        const transaccionesPorEdad = await fetchWithRetry(`${DATA_API_URL}/transacciones-grupo-edad-operacion`);
        const ticketMedio = await fetchWithRetry(`${DATA_API_URL}/ticket-medio-qr-app`);
        const transaccionesPorHora = await fetchWithRetry(`${DATA_API_URL}/transacciones-por-horas`);
        const mapaClienteZona = await fetchWithRetry(`${DATA_API_URL}/mapa-usuarios-zona`);


        const responseData = {
            usuariosPorEdad,
            evolucionAltas,
            porcentajePagos,
            transaccionesPorEdad,
            ticketMedio,
            transaccionesPorHora,
            mapaClienteZona
        };


        await redisClient.set(CACHE_KEY, JSON.stringify(responseData), {
            EX: CACHE_EXPIRATION, 
        });

        console.log('Datos guardados en Redis');
        return responseData;

    } catch (error) {
        console.error('Error in clientController:', error.message);
        if (error.response) {
            console.error('Response error data:', error.response.data);
            console.error('Response error status:', error.response.status);
        }
        throw {
            status: error.response?.status || 500,
            message: error.response?.data?.error || 'Error al obtener los datos de clientes',
            details: error.message
        };
    }
};


export const clientController = {
    getClientPageData
};

export default clientController;