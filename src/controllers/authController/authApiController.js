import authController from "./authController.js";
import jwt from "../../config/jwt.js";


async function login(req, res) {
    try {
        const { email, password } = req.body;
        const user = await authController.login(email, password);

        if (!user) {
            throw new error.USER_NOT_FOUND();
        }
        const token = jwt.sign({ });
        res.json({ token});
    } catch (error) {
        console.error(error);
        error.status ? res.status(error.status) : res.status(500);

        res.json({ message: error.message });
    }
}


export default {
    login
}