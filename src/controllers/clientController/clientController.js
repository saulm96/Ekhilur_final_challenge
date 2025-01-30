// clientController.js
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const DATA_API_URL = `http://${process.env.DATA_API_APP_HOST}:${process.env.DATA_API_APP_PORT}`;

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

export const clientController = {
    getAllClients
};

export default clientController;