import userController from "../userController/userController.js";
import {verifyPassword} from '../../config/bcrypt.js';
import userError from "../../utils/errors/userErrors.js";

async function login(email, password){
    const user = await userController.getUserByEmail(email);
    
    if(!user) throw new userError.USER_NOT_FOUND;

    const isPasswordValid = await verifyPassword(password, user.password);

    if(!isPasswordValid) throw new userError.INVALID_PASSWORD;

    return user;
}


export default {
    login
}

