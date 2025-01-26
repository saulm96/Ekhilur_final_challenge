class USER_NOT_FOUND extends Error{
    constructor(){
        super("User not found");
        this.status = 404;
    }
}

class INVALID_PASSWORD extends Error{
    constructor(){
        super("Invalid password");
        this.status = 401;
    }
}



export default {
    USER_NOT_FOUND,
    INVALID_PASSWORD
};