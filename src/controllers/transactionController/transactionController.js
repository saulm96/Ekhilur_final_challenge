import  axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const DATA_API_URL = `http://${process.env.DATA_API_APP_HOST}:5000`;

const getSumByTransactionsType = async () => {
    try {
        const response = await axios.get(`${DATA_API_URL}/suma_por_tipo_de_transaccion`);
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

export { getSumByTransactionsType };


export const transactionController = {
    getSumByTransactionsType
};

export default transactionController;