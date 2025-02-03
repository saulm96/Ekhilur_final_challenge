// clientController.js
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const DATA_API_URL = `http://${process.env.DATA_API_APP_HOST}:5000`;

const getAllClients = async () => {
    try {
        const response = await axios.get(`${DATA_API_URL}/usuarios`);
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
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
};

const getClientPageData = async () => {
    try {
        
        // Usar las rutas correctas que existen en la API Flask
        const usuariosPorEdad = await fetchWithRetry(`${DATA_API_URL}/cantidad-usuarios-grupo-edad`);
        
        const evolucionAltas = await fetchWithRetry(`${DATA_API_URL}/evolucion-altas-mes`);
        
        const porcentajePagos = await fetchWithRetry(`${DATA_API_URL}/porcentaje-pagos-qr-app`);
        
        const transaccionesPorEdad = await fetchWithRetry(`${DATA_API_URL}/transacciones-grupo-edad-operacion`);
        
        const ticketMedio = await fetchWithRetry(`${DATA_API_URL}/ticket-medio-qr-app`);

        /* const ususariosUnicos = await fetchWithRetry(`${DATA_API_URL}/usuarios-unicos-mensuales-semana-dia`); */
        
        const transaccionesPorHora = await fetchWithRetry(`${DATA_API_URL}/transacciones-por-horas`); // hay que borrar

        

        const responseData = {
            usuariosPorEdad,
            evolucionAltas,
            porcentajePagos,
            transaccionesPorEdad,
            ticketMedio,
            transaccionesPorHora,
           /*  ususariosUnicos */
            
        };

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