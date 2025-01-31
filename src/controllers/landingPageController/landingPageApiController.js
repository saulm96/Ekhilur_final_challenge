import landingPageController from './landingPageController.js';

async function getLandingPageData(req, res) {
    try {
        console.log('API Controller: Getting landing page data');
        const landingData = await landingPageController.getLandingPageData();
        console.log('API Controller: Got landing page data');
        res.status(200).json(landingData);
    } catch (error) {
        console.error('API Controller Error:', error);
        res.status(error.status || 500).json({ 
            error: error.message || 'Error al obtener los datos de la landing page'
        });
    }
}

export const landingPageApiController = {
    getLandingPageData
};

export default landingPageApiController;