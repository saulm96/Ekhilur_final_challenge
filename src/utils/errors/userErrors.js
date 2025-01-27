
class UserError extends Error {
    constructor(messages, status) {
        super();
        this.messages = messages;
        this.status = status;
        this.message = messages;

        Object.setPrototypeOf(this, new.target.prototype);
    }
    toJSON() {
        return {
            message: this.messages,
            status: this.status,
        };
    }

    get errorResponse() {
        return this.toJSON();
    }
}

class USER_NOT_FOUND extends UserError {
    constructor() {
        const messages = {
            ES: "Usuario no encontrado",
            EUS: "Ez da erabiltzailea aurkitu"
        };
        super(messages, 404);
    }
}

class INVALID_PASSWORD extends UserError {
    constructor() {
        const messages = {
            ES: "Contraseña incorrecta",
            EUS: "Pasahitza ez da zuzena"
        };
        super(messages, 401);
    }
}

export default {
    USER_NOT_FOUND,
    INVALID_PASSWORD
};