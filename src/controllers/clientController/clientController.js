// clientController.js
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const DATA_API_URL = `http://${process.env.DATA_API_APP_HOST}:5000`;

const getAllClients = async () => {
    try {
        console.log(`Trying to fetch clients from: ${DATA_API_URL}/usuarios`);
        const response = await axios.get(`${DATA_API_URL}/usuarios`);
        console.log('Response received:', response.data);
        return response.data;
    } catch (error) {
        console.error('Error in clientController:', error.message);
        if (error.response) {
            console.error('Response error data:', error.response.data);
            console.error('Response error status:', error.response.status);
        }
        throw {
            status: error.response?.status || 500,
            message: error.response?.data?.error || 'Error al obtener los clientes'
        };
    }
};


const fetchWithRetry = async (url, retries = 3, delay = 1000) => {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await axios.get(url);
            return response.data;
        } catch (error) {
            if (i === retries - 1) throw error; // Si es el último intento, propagar el error
            console.log(`Intento ${i + 1} fallido para ${url}, reintentando...`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
};



export const clientController = {
    getAllClients
};

export default clientController;