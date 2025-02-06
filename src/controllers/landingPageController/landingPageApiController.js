import landingPageController from './landingPageController.js';

async function getLandingPageData(req, res) {
    try {
        const landingData = await landingPageController.getLandingPageData();
        res.status(200).json(landingData);
    } catch (error) {
        console.error('API Controller Error:', error);
        res.status(error.status || 500).json({ 
            error: error.message || 'Error al obtener los datos de la landing page'
        });
    }
}


async function getUpdatedLandingPage(req, res){
    try {
        const updatedLandingPage = await landingPageController.getUpdatedLandingPage();
        res.status(200).json(updatedLandingPage);
    } catch (error) {
        console.error('API Controller error', error);
        res.status(error.status || 500).json({
            error: error.message || 'Error al obtener las transacciones actualizadas'
        })
    }
}
export const landingPageApiController = {
    getLandingPageData,
    getUpdatedLandingPage
};

export default landingPageApiController;