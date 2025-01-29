import { createClient } from 'redis';

const redisClient = createClient({
    url: `redis://:${process.env.REDIS_PASSWORD}@${process.env.REDIS_HOST}:${process.env.REDIS_PORT}`,
    socket: {
        reconnectStrategy: retries => Math.min(retries * 50, 1000)
    },
    retry_strategy: function (options) {
        if (options.total_retry_time > 1000 * 60 * 60) {
            return new Error('Retry time exhausted');
        }
        return Math.min(options.attempt * 100, 3000);
    }
});

redisClient.on('error', err => console.error('Redis error: ', err));

const connectRedis = async () => {
    try {
        await redisClient.connect();
        console.log('Redis connected successfully');
    } catch (err) {
        console.error('Redis connection error:', err);
        setTimeout(connectRedis, 5000);
    }
};

connectRedis();

export const blackListToken = async (token) => {
    const key = `blacklist:${token}`;
    await redisClient.set(key, 'true', {
        EX: 24 * 60 * 60
    });
    console.log('Token blacklisted:', token);
};

export const isTokenBlackListed = async (token) => {
    try {
        const key = `blacklist:${token}`;
        const result = await redisClient.get(key);
        return result === 'true';
    } catch (error) {
        console.error('Redis blacklist check error:', error);
        return false;
    }
};

export { redisClient };