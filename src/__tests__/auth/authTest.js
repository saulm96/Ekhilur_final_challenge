import request from 'supertest';
import  app  from '../../index.js';
import TwoFactorAuth from '../../config/2fa-auth.js';
import  User  from '../../models/userModel.js';

describe('2FA Authentication', () => {
    let loginToken;

    beforeAll(async () => {
        // Login and store token for tests
        const loginRes = await request(app)
            .post('/api/auth/login')
            .send({
                email: 'ekhiluradmin@gmail.com',
                password: 'ekh1luR@'
            });
        loginToken = loginRes.body.token;
    });

    test('Setup 2FA', async () => {
        const setupRes = await request(app)
            .post('/api/auth/2fa/setup')
            .set('Authorization', `Bearer ${loginToken}`)
            .send();

        expect(setupRes.status).toBe(200);
        expect(setupRes.body).toHaveProperty('token');
    });

    test('Verify 2FA', async () => {
        const user = await User.findOne({ 
            where: { email: 'ekhiluradmin@gmail.com' }
        });
        
        const token = TwoFactorAuth.generateToken(user.two_factor_secret);

        const verifyRes = await request(app)
            .post('/api/auth/2fa/verify')
            .set('Authorization', `Bearer ${loginToken}`)
            .send({ token });

        expect(verifyRes.status).toBe(200);
    });
});