import { getAllBlackListedTokens}  from "./adminInfoController.js";

export async function getAllBlacklistedTokens(req, res){
    try {
        const tokens = await getAllBlackListedTokens();
        if(!tokens){
            return res.status(404).json({message: "No blacklisted tokens found"});
        }
        return res.status(200).json(tokens);
    } catch (error) {
        console.error(error);
        return res.status(500).json({message: "Internal Server Error"});
    }
}

