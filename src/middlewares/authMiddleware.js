import jwt from "../config/jwt.js";
import checkIfTheTokenExistsAndTheType from "../utils/errors/authErrorHandle.js";

export async function isAutenticated(req, res, next){
    try {
        const authorization = checkIfTheTokenExistsAndTheType(req.headers.authorization);
        const token = authorization.split(' ')[1];
        
        const verifiedToken = jwt.verify(token);

        if(!verifiedToken){
            return res.status(401).json({ message: 'Invalid token' });
        }

        next();
    } catch (error) {
        return res.status(401).json({ message: 'Something happened while verifying the token' });
    }
}

