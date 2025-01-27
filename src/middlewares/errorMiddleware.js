import  UserError  from '../utils/errors/userErrors.js';

export const errorHandler = (err, req, res, next) => {
    if (err instanceof UserError.INVALID_PASSWORD || err instanceof UserError.USER_NOT_FOUND) {
        return res.status(err.status).json({
            error: true,
            message: err.messages
        })
    }
    else {
        res.status(500).json({ 
            error:true,
            message: 'Something went wrong' });
    }
    next();
}
