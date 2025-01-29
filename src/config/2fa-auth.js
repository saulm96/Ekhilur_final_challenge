import twofactor from 'node-2fa';

class TwoFactorAuth {
    generateSecret(userName, serviceName = 'EkhilurAdminWeb') {
        const secret = twofactor.generateSecret({
            name: serviceName,
            account: userName,
        });
        return secret.secret;
    }

    generateToken(secret) {
        const token = twofactor.generateToken(secret)
        return token ? token.token : null;
    }

    verifyToken(secret, token) {
        return twofactor.verifyToken(secret, token);
    }
}

export default new TwoFactorAuth();