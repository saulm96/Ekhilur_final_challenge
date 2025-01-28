import jwt from "../config/jwt.js";
import { isTokenBlackListed } from "../utils/redisUtils/cookiesBlackList.js";

export async function isAuthenticated(req, res, next){
    try {
        const token = req.cookies?.authToken;
        if(!token){
            return res.status(401).json({message: "Unauthorized"});
        }

        const isBlacklisted = await isTokenBlackListed(token);
        if(isBlacklisted){
            return res.status(401).json({message: "The token is in the blacklist!!!!"});
        }

        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        req.user = decoded;
        next()
    } catch (error) {
        console.error(error);
        return res.status(500).json({message: "ups! something went wrong"});
    }
}

