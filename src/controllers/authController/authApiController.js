import authController from "./authController.js";
import userController from "../userController/userController.js";
import jwt from "../../config/jwt.js";
import { blackListToken } from "../../utils/redisUtils/cookiesBlackList.js";
import error from "../../utils/errors/userErrors.js";
import speakeasy from "speakeasy";

async function login(req, res) {
    try {
        const { email, password } = req.body;

        if (!email || !password) {
            throw new error.MISSING_CREDENTIALS();
        }

        // Validate credentials
        const user = await authController.login(email, password);
        if (!user) {
            throw new error.INVALID_CREDENTIALS();
        }

        const checkingUser = await userController.getUserByEmail(email);

        if (!checkingUser.two_factor_secret) {
            // Generate 2FA token
            const secret = speakeasy.generateSecret({
                name: `MyApp: ${user.email}`,
                length: 10,
            });

            await user.update({
                two_factor_secret: secret.base32
            });
        }

        return res.json({
            success: true,
            secret: user.secret,
            message: "Please enter this secret in Google Authenticator and verify the token to complete login!"
        });

    } catch (error) {
        console.error(error);
        error.status ? res.status(error.status) : res.status(500);
        res.json({ message: error.message });
    }
}

async function verify2FA(req, res) {
    try {
        const { tokenF2A, email } = req.body;

        if (!tokenF2A || !email) {
            throw new error.MISSING_CREDENTIALS();
        }

        const user = await userController.getUserByEmail(email);
        if (!user || !user.two_factor_secret) {
            throw new error.INVALID_CREDENTIALS();
        }

        const isValid = speakeasy.totp.verify({
            secret: user.two_factor_secret,
            encoding: "base32",
            token: tokenF2A
        });
        if (!isValid) {
            throw new error.INVALID_2FA_TOKEN();
        }

        // Enable 2FA and complete login
        await user.update({
            two_factor_enabled: true
        });

        const authToken = jwt.sign({
            userId: user.user_id
        });

        res.cookie("authToken", authToken, {
            httpOnly: true,
            secure: true,
            sameSite: "strict",
            maxAge: 3600000,
            path: "/"
        });

        return res.json({
            success: true,
            message: "Login successful"
        });
    } catch (error) {
        console.error(error);
        error.status ? res.status(error.status) : res.status(500);
        res.json({ message: error.message });
    }
}

async function logout(req, res) {
    try {
        const token = req.cookies?.authToken;
        console.log('cookie recibed: ', req.cookies);
        console.log('token recibed: ', token);
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
    logout,
    verify2FA
}