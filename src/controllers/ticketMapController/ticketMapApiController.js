import  ticketMapController  from "./ticketMapController.js"

async function getTicketMap(req, res) {
    try {
        const ticketMap = await ticketMapController.getTicketMap();
        res.status(200).json(ticketMap);
    } catch (error) {
        console.error('API Controller Error:', error);
        res.status(error.status || 500).json({ 
            error: error.message || 'Error al obtener el mapa de tickets'
        });
    }
}

export const ticketMapApiController = {
    getTicketMap
}

export default ticketMapApiController