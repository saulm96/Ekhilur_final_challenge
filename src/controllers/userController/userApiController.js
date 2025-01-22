import userController from './userController.js';

async function getAllUsers(req, res) {
    try {
        const users = await userController.getAllUsers();
        return res.status(200).json(users);
    } catch (error) {
        error.status ? res.status(error.status).json(error)
            : res.status(500).json(error);
    }
}

async function getUserById(req, res) {
    try {
        const user = await userController.getUserById(req.params.id);
        return res.status(200).json(user);
    } catch (error) {
        error.status ? res.status(error.status).json(error)
            : res.status(500).json(error);
    }
}

export const functions = {
    getAllUsers,
    getUserById,
};

export default functions;