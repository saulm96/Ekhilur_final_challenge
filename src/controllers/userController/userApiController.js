import userController from './userController.js';

async function getUserByEmail(req, res){
    try{
        const user = await userController.getUserByEmail(req.params.email);

        res.status(200).send(user);
    }
    catch(error){
        res.status(404).send(error.message);
    }
}

export const functions = {
    getUserByEmail,
};

export default functions;