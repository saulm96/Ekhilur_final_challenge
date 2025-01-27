import authController from "./authController.js";
import jwt from "../../config/jwt.js";


async function login(req, res) {
    try {
        const { email, password } = req.body;
        const user = await authController.login(email, password);

        if (!user) {
            throw new error.USER_NOT_FOUND();
        }

        const token = jwt.sign({
            userId: user.user_id
        });

        res.cookie( "authToken", token,{
            httpOnly: true,
            secure: true,
            sameSite: "strict",
            maxAge: 3600000,
            path: "/"
        });

        return res.json({
            success: true, 
            token
        })
    } catch (error) {
        console.error(error);
        error.status ? res.status(error.status) : res.status(500);

        res.json({ message: error.message });
    }
}


export default {
    login
}