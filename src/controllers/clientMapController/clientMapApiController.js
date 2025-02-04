import clientMapController from "./clientMapController.js";

async function getClientMap(req, res) {
    try {
        const clientMap = await clientMapController.getClientMap();
        res.status(200).json(clientMap);
    } catch (error) {
        console.error('API Controller Error:', error);
        res.status(error.status || 500).json({ 
            error: error.message || 'Error al obtener el mapa de clientes'
        });
    }
}

export const clientMapApiController = {
    getClientMap
}

export default clientMapApiController