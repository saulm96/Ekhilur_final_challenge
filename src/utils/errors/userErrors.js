
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

class INVALID_2FA_TOKEN extends UserError {
    constructor() {
        const messages = {
            ES: "Token de autenticación de dos factores inválido",
            EUS: "Bi faktoreetako autentifikazio tokena ez da zuzena"
        };
        super(messages, 401);
    }
}

class MISSING_CREDENTIALS extends UserError {
    constructor() {
        const messages = {
            ES: "Faltan credenciales",
            EUS: "Kredentzialak falta dira"
        };
        super(messages, 400);
    }
}

class INVALID_CREDENTIALS extends UserError {
    constructor() {
        const messages = {
            ES: "Credenciales inválidas",
            EUS: "Kredentzialak ez dira zuzenak"
        };
        super(messages, 400);
    }
}

class TWO_FACTOR_NOT_SETUP extends UserError {
    constructor() {
        const messages = {
            ES: "La autenticación de dos factores no está configurada",
            EUS: "Bi faktoreetako autentifikazioa ez dago konfiguratuta"
        };
        super(messages, 400);
    }
}

export default {
    USER_NOT_FOUND,
    INVALID_PASSWORD,
    INVALID_2FA_TOKEN,
    MISSING_CREDENTIALS,
    INVALID_CREDENTIALS,
    TWO_FACTOR_NOT_SETUP
};