import axios from 'axios';
import dotenv from 'dotenv';


dotenv.config();

const DATA_API_URL = `http://${process.env.DATA_API_APP_HOST}:5000`;

const getTicketMap = async () => {
    try {
        const response = await axios.get(`${DATA_API_URL}/mapa-ticket-medio`);
        return response.data;
    } catch (error) {
        console.error('Error in ticketMapController:', error.message);
        if (error.response) {
            console.error('Response error data:', error.response.data);
            console.error('Response error status:', error.response.status);
        }
        throw {
            status: error.response?.status || 500,
            message: error.response?.data?.error || 'Error al obtener el mapa de tickets'
        };
    }


};


export const ticketMapController = {
    getTicketMap
}

export default ticketMapController