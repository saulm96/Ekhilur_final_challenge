import predictController from "./predictController.js";


async function getPredictions(req, res) {
    try {
        const predictions = await predictController.getPredictions();
        res.status(200).json(predictions);
        
    } catch (error) {
        console.error('API Controller Error:', error);
        res.status(error.status || 500).json({
            error: error.message || 'Error al obtener las predicciones'
        })
    }
}

export const predictApiController = {
    getPredictions
}

export default predictApiController