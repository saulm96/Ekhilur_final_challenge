import {Router} from 'express';
import { isAuthenticated } from "../../middlewares/authMiddleware.js";
import authApiController from "../../controllers/authController/authApiController.js";
import { getAllBlacklistedTokens } from "../../controllers/adminInfoController/adminInfoApiController.js";


import userRoute from "./userApiRoutes.js";

const router = Router();


router.get("/blacklist", getAllBlacklistedTokens);

router.post("/login", authApiController.login);
router.post("/2fa/verify" ,authApiController.verify2FA);
router.post("/logout",isAuthenticated ,authApiController.logout); 


router.use("/user",userRoute);




export default router;

