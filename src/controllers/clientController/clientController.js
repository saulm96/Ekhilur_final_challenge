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
            if (i === retries - 1) throw error;
            console.log(`Intento ${i + 1} fallido para ${url}, reintentando...`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
};

const getClientPageData = async () => {
    try {
        console.log('Fetching client page data from DATA API');
        
        // Usar las rutas correctas que existen en la API Flask
        const usuariosPorEdad = await fetchWithRetry(`${DATA_API_URL}/cantidad-usuarios-grupo-edad`);
        console.log('Users by age group data fetched successfully');
        
        const evolucionAltas = await fetchWithRetry(`${DATA_API_URL}/evolucion-altas-mes`);
        console.log('User registration evolution data fetched successfully');
        
        const porcentajePagos = await fetchWithRetry(`${DATA_API_URL}/porcentaje-pagos-qr-app`);
        console.log('Payment percentage data fetched successfully');
        
        const transaccionesPorEdad = await fetchWithRetry(`${DATA_API_URL}/transacciones-grupo-edad-operacion`);
        console.log('Transactions by age group data fetched successfully');
        
        const ticketMedio = await fetchWithRetry(`${DATA_API_URL}/ticket-medio-qr-app`);
        console.log('Average ticket data fetched successfully');
        
        const transaccionesPorHora = await fetchWithRetry(`${DATA_API_URL}/transacciones-por-horas`);
        console.log('Transactions by hour data fetched successfully');

        const responseData = {
            usuariosPorEdad,
            evolucionAltas,
            porcentajePagos,
            transaccionesPorEdad,
            ticketMedio,
            transaccionesPorHora
        };

        console.log('All client page data fetched and consolidated successfully');
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
    getAllClients,
    getClientPageData
};

export default clientController;