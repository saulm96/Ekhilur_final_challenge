import userController from './userController.js';


async function getAllUsers(req, res){
    try{
        const users = await userController.getAllUsers();
        res.status(200).send(users);
    }
    catch(error){
        error.status ? res.status(error.status) : res.status(500);
        res.json({ error: error.message });        
    }
}

async function getUserByEmail(req, res){
    try{
        const user = await userController.getUserByEmail(req.params.email);
        res.status(200).send(user);
    }
    catch(error){
        error.status ? res.status(error.status) : res.status(500);
        res.json({ error: error.message });        
    }
}

async function getUserData(req, res){
    try{
        const user = await userController.getUserData(req.params.id);

        res.status(200).send(user);
    }
    catch(error){
        error.status ? res.status(error.status) : res.status(500);
        res.json({ error: error.message });        
    }
}


export const functions = {
    getUserByEmail,
    getUserData,
    getAllUsers,
};

export default functions;