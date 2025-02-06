import transactionController from "./transactionController.js";


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

async function getUpdatedTransactions(req, res) {
    try {
        const updatedTransactions = await transactionController.getUpdatedTransactions();
        res.status(200).json(updatedTransactions);
    } catch (error) {
        console.error('API Controller error', error);
        res.status(error.status || 500).json({
            error: error.message || 'Error al obtener las transacciones actualizadas'
        })
    }
}
export const transactionApiController = {
    getUpdatedTransactions,
    getTransictionPageData
};

export default transactionApiController