import { redisClient } from "../../utils/redisUtils/cookiesBlackList.js";
export async function getAllBlackListedTokens() {
    try {
        const keys = await redisClient.keys("blacklist*");
        const tokens = keys.map(key => key.replace("blacklist:", ""));
        return tokens;
    } catch (error) {
        console.error("Error getting all blacklisted tokens:", error);
        return [];

    }
};
