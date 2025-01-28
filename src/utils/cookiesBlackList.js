import { createClient } from "redis";

const redisClient = createClient({
    url: `redis://${process.env.REDIS_HOST}:${process.env.REDIS_PORT}`,
    socket: {
        reconnectStrategy: retries => Math.min(retries * 50, 1000)
    },
    retry_strategy: function (options) {
        if (options.total_retry_time > 1000 * 60 * 60) {
            return new Error('Retry time exhausted');
        }
        return Math.min(options.attempt * 100, 3000);
    }
})

redisClient.on('error', err => console.error('Redis error: ', err));
await redisClient.connect();

export const blackListToken = async (token) => {
    const key = `blacklist:${token}`;
    await redisClient.set(key, 'true', {
        EX: 24 * 60 * 60
    });
};


export const isTokenBlackListed = async (token) => {
    const key = `blacklist:${token}`;
    const result = await redisClient.get(key);
    return result === 'true';
}



export default redisClient;
