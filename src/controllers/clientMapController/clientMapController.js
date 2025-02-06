import axios from 'axios';
import dotenv from 'dotenv';
import { redisClient } from '../../utils/redisUtils/cookiesBlackList.js';
import { fetchWithRetry } from '../../utils/redisUtils/fetchWithCache.js';

dotenv.config();

const CACHE_KEY = 'clients';
const CACHE_EXPIRATION = 36000; // 10 horas 

const DATA_API_URL = `http://${process.env.DATA_API_APP_HOST}:5000`;

const getClientMap = async () => {
try {
    const cachedData = await redisClient.get(CACHE_KEY)
    const response = fetchWithRetry(`${DATA_API_URL}/mapa-usuarios-zona`);
    return response.data;
} catch (error) {
    console.error('Error in clientMapController:', error.message);
    if (error.response) {
        console.error('Response error data:', error.response.data);
        console.error('Response error status:', error.response.status);
    }
    throw {
        status: error.response?.status || 500,
        message: error.response?.data?.error || 'Error al obtener el mapa de clientes'
    };
}

}

export const clientMapController = {
    getClientMap
};

export default clientMapController;

