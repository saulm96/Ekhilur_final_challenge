import User from "../../models/userModel.js";
import userError from "../../utils/errors/userErrors.js";

async function getUserByEmail(email){
    const user = await User.findOne({where: {email: email}});
    if(!user){
        throw new userError.USER_NOT_FOUND();
    }
    return user;
}

async function getUserData(id){
    const user = await User.findOne({where: {user_id: id}});
    if(!user){
        throw new userError.USER_NOT_FOUND();
    }
    return user;
}

export const functions = {
    getUserByEmail,
    getUserData
};

export default functions;

