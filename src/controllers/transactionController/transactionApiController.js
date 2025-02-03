import transactionController from "./transactionController.js";

async function getSumByTransactionsType(req, res) {
    try {
        const transactions = await transactionController.getSumByTransactionsType();
        res.status(200).json(transactions);
    } catch (error) {
        console.error('API Controller Error:', error);
        res.status(error.status || 500).json({ 
            error: error.message || 'Error al obtener las transacciones'
        });
    }
}

async function getTransictionPageData(req, res) {
    try {
        const transactions = await transactionController.getTransictionPageData();
        res.status(200).json(transactions);
    } catch (error) {
        console.error('API Controller Error:', error);
        res.status(error.status || 500).json({ 
            error: error.message || 'Error al obtener las transacciones'
        });
    }
}

export const transactionApiController = {
    getSumByTransactionsType,
    getTransictionPageData
};

export default transactionApiController