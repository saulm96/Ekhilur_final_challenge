import dotenv from 'dotenv';
import { fetchWithRetry } from '../../utils/redisUtils/fetchWithCache.js';
import { redisClient } from '../../utils/redisUtils/cookiesBlackList.js';

dotenv.config();
const CACHE_KEY = 'predictions';
const CACHE_EXPIRATION = 36000; 

const DATA_API_URL = `http://${process.env.DATA_API_APP_HOST}:5000`;

const getPredictions = async () => {
    try {
        const cachedData = await redisClient.get(CACHE_KEY);
        if (cachedData) {
            console.log('Datos obtenidos de Redis');
            return JSON.parse(cachedData);
        }
        const response = await fetchWithRetry(`${DATA_API_URL}/predict`);
        await redisClient.set(CACHE_KEY, JSON.stringify(response), { EX: CACHE_EXPIRATION });
        console.log("Datos guardados en Redis");
        return response; 
    } catch (error) {
        console.error('Error in predictController:', error.message);
        if (error.response) {
            console.error('Response error data:', error.response.data);
            console.error('Response error status:', error.response.status);
        }
        throw {
            status: error.response?.status || 500,
            message: error.response?.data?.error || 'Error al obtener las predicciones'
        };
    }
};

const getUpdatePredictions = async () => {
    try {
        // Borrar la clave de caché para que se actualice
        await redisClient.del(CACHE_KEY);
        console.log('Datos de predicciones eliminados de Redis');
        const updatedPredictions = await getPredictions();

        return updatedPredictions;
    } catch (error) {
        console.error('Error in predictController:', error.message);
    }
}

export const predictController = {
    getPredictions,
    getUpdatePredictions
};

export default predictController;
