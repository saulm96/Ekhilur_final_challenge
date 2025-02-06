// clientApiController.js
import clientController from './clientController.js';


async function getClientPageData(req, res) {
    try {
        const clientData = await clientController.getClientPageData();
        res.status(200).json(clientData);
    } catch (error) {
        console.error('API Controller Error:', error);
        res.status(error.status || 500).json({ 
            error: error.message || 'Error al obtener los datos de la landing page'
        });
    }
}


async function getUpdatedClientPageData(req, res){
    try {
        const updatedClientPageData = await clientController.getUpdatedClientPageData();
        res.status(200).json(updatedClientPageData);
    } catch (error) {
        console.error('API Controller error', error);
        res.status(error.status || 500).json({
            error: error.message || 'Error al obtener las transacciones actualizadas'
        })
    }
}
export const clientApiController = {
    getClientPageData,
    getUpdatedClientPageData
};

export default clientApiController;