import speakeasy from "speakeasy";

const TwoFactorAuth = {
    generateSecret: ()=>{
        return speakeasy.generateSecret().base32;
    },

    verifyToken: (secret,token) => {
        return speakeasy.totp.verify({
            secret,
            encoding: 'base32',
            token
        });
    }
}

export default TwoFactorAuth;