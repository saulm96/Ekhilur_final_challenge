import User from "../../models/userModel.js";
import error from "../../utils/errors/userErrors.js";

async function getUserByEmail(email){
    const user = await User.findOne({where: {email: email}});

    if(!user){
        throw new error.USER_NOT_FOUND();
    }
    return user;
}

export const functions = {
    getUserByEmail,
};

export default functions;

