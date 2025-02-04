import  axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const DATA_API_URL = `http://${process.env.DATA_API_APP_HOST}:5000`;


const fetchWithRetry = async (url, retries = 3, delay = 1000) => {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await axios.get(url);
            return response.data;
        } catch (error) {
            if (i === retries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
};

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

        const transactions = await fetchWithRetry(`${DATA_API_URL}/suma-por-tipo-de-transaccion`);

        const totalWastedVsCashBack = await fetchWithRetry(`${DATA_API_URL}/gasto-total-vs-cashback-total`);
        
        const mobileAverage = await fetchWithRetry(`${DATA_API_URL}/medias-moviles`);

        const transaccionesEntreSemanaYFinDeSemana = await fetchWithRetry(`${DATA_API_URL}/total-entresemana-findesemana`);  

        const transaccionesPorHora = await fetchWithRetry(`${DATA_API_URL}/transacciones-por-horas`);
        
        const responseData = {
            transactions,
            totalWastedVsCashBack,
            mobileAverage,
            transaccionesEntreSemanaYFinDeSemana,
            transaccionesPorHora
        };
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