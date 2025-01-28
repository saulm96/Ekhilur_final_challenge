import authController from "./authController.js";
import jwt from "../../config/jwt.js";
import { blackListToken } from "../../utils/cookiesBlackList.js";


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

        res.cookie("authToken", token, {
            httpOnly: true,
            secure: true,
            sameSite: "strict",
            maxAge: 3600000,
            path: "/"
        });


        return res.json({
            success: true,
        })
    } catch (error) {
        console.error(error);
        error.status ? res.status(error.status) : res.status(500);

        res.json({ message: error.message });
    }
}

async function logout(req, res) {
    try {
        const token = req.cookies?.authToken;
        if (!token) {
            return res.status(401).json({ message: "Unauthorized" });
        }

        await blackListToken(token);

        res.clearCookie("authToken", {
            httpOnly: true,
            secure: true,
            sameSite: "strict",
        });

        return res.status(200).json({
            succes: true,
            message: 'Logged out successfully'
        })

    } catch (error) {
        console.error(error);
        return res.status(500).json({ message: "Internal Server Error" });
    }
}

export default {
    login,
    logout
}