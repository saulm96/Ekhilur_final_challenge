import User from "../../models/userModel.js";

async function getAllUsers(){
    const users = await User.findAll();
    return users;
}

async function getUserById(id){
    const user = await User.findByPk(id);
    if(!user){
        throw userError.userNotFound;
    }
    return user;
}

export const functions = {
    getAllUsers,
    getUserById,
};

export default functions;

