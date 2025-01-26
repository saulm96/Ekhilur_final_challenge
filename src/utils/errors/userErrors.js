class UserError extends Error {
    constructor(messages, status){
        super(JSON.stringify(messages));
        this.messages = messages;
        this.status = status;
    }
}

class USER_NOT_FOUND extends UserError{
    constructor(){
        const messages = {
            ES: "Usuario no encontrado",
            EUS: "Ez da erabiltzailea aurkitu"
        };
        super(messages, 404);
    }
}

class INVALID_PASSWORD extends UserError{
    constructor(){
        const messages = {
            ES: "Contraseña incorrecta",
            EUS: "Pasahitza okerra"
        };
        super(messages, 401);
    }
}

export default {
    USER_NOT_FOUND,
    INVALID_PASSWORD
};