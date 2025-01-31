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


async function getClientPageData(req, res) {
    try {
        console.log('API Controller: Getting client page data');
        const clientData = await clientController.getClientPageData();
        console.log('API Controller: Got client page data');
        res.status(200).json(clientData);
    } catch (error) {
        console.error('API Controller Error:', error);
        res.status(error.status || 500).json({ 
            error: error.message || 'Error al obtener los datos de la landing page'
        });
    }
}

export const clientApiController = {
    getAllClients,
    getClientPageData
};

export default clientApiController;