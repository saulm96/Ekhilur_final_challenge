class UserError extends Error {
    constructor(message, statusCode = 500) {
        super(message);
        this.name = 'UserError';
        this.statusCode = statusCode;
    }
}

class USER_NOT_FOUND extends UserError {
    constructor() {
        super('User not found', 404);
        this.name = 'UserNotFoundError';
    }
} 

class INVALID_PASSWORD extends UserError {
    constructor() {
        super('Invalid password', 401);
        this.name = 'InvalidPasswordError';
    }
}

export default {
    USER_NOT_FOUND,
    INVALID_PASSWORD
};