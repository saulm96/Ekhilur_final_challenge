import twofactor from 'node-2fa';

class TwoFactorAuth {
    generateSecret(userName, serviceName = 'EkhilurAdminWeb') {
        return twofactor.generateSecret({
            name: serviceName,
            account: userName
        })
    }

    generateToken(secret) {
        return twofactor.generateToken(secret);
    }

    verifyToken(secret, token) {
        const result = twofactor.verifyToken(secret, token);

        return result;

    }
}

export default new TwoFactorAuth();