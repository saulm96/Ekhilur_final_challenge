// clientApiController.js
import clientController from './clientController.js';

async function getAllClients(req, res) {
    try {
        console.log('API Controller: Getting all clients');
        const clients = await clientController.getAllClients();
        console.log('API Controller: Got clients:', clients);
        res.status(200).json(clients);
    } catch (error) {
        console.error('API Controller Error:', error);
        res.status(error.status || 500).json({ 
            error: error.message || 'Error al obtener los clientes'
        });
    }
}

export const clientApiController = {
    getAllClients
};

export default clientApiController;