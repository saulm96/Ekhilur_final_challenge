import  axios from 'axios';
import dotenv from 'dotenv';
import { fetchWithRetry } from '../../utils/redisUtils/fetchWithCache.js';
import { redisClient } from '../../utils/redisUtils/cookiesBlackList.js';

dotenv.config();

const CACHE_KEY = 'transactions';
const CACHE_EXPIRATION = 36000; // 10 horas

const DATA_API_URL = `http://${process.env.DATA_API_APP_HOST}:5000`;



const getSumByTransactionsType = async () => {
    try {
        const response = await axios.get(`${DATA_API_URL}/suma-por-tipo-de-transaccion`);
        return response.data;
    } catch (error) {
        console.error('Error in transactionController:', error.message);
        if (error.response) {
            console.error('Response error data:', error.response.data);
            console.error('Response error status:', error.response.status);
        }
        throw {
            status: error.response?.status || 500,
            message: error.response?.data?.error || 'Error al obtener las transacciones'
        };
    }
};


const getTransictionPageData = async () => {
    try{

        const cachedData = await redisClient.get(CACHE_KEY);
        if (cachedData) {
            console.log('Datos obtenidos de Redis');
            return JSON.parse(cachedData);
        }
        console.log('Datos no encontrados en Redis, llamando a la API externa...');

        const transactions = await fetchWithRetry(`${DATA_API_URL}/suma-por-tipo-de-transaccion`);

        const totalWastedVsCashBack = await fetchWithRetry(`${DATA_API_URL}/gasto-total-vs-cashback-total`);
        
        const mobileAverage = await fetchWithRetry(`${DATA_API_URL}/medias-moviles`);

        const transaccionesEntreSemanaYFinDeSemana = await fetchWithRetry(`${DATA_API_URL}/total-entresemana-findesemana`);  

        const transaccionesPorHora = await fetchWithRetry(`${DATA_API_URL}/transacciones-por-horas`);

        const mapTicketMedio = await fetchWithRetry(`${DATA_API_URL}/mapa-ticket-medio`);
        
        const responseData = {
            transactions,
            totalWastedVsCashBack,
            mobileAverage,
            transaccionesEntreSemanaYFinDeSemana,
            transaccionesPorHora,
            mapTicketMedio
        };

        await redisClient.set(CACHE_KEY, JSON.stringify(responseData), { EX: CACHE_EXPIRATION });
        console.log('Datos almacenados en Redis');
        return responseData;


     } catch (error) {
            console.error('Error in transactionController:', error.message);
        if (error.response) {
            console.error('Response error data:', error.response.data);
            console.error('Response error status:', error.response.status);
        }
        throw {
            status: error.response?.status || 500,
            message: error.response?.data?.error || 'Error al obtener las transacciones',
            details: error.message
        };  
    }
};
    



export const transactionController = {
    getSumByTransactionsType,
    getTransictionPageData
};

export default transactionController;