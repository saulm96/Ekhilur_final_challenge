import {Router} from 'express';
import { isAuthenticated } from "../../middlewares/authMiddleware.js";
import authApiController from "../../controllers/authController/authApiController.js";
import { getAllBlacklistedTokens } from "../../controllers/adminInfoController/adminInfoApiController.js";



import userRoute from "./userApiRoutes.js";
import clientRouter from "./clientApiRouter.js";
import landingPageApiRouter from "./landingPageApiRouter.js";
import transactionApiRouter from "./transactionApiRouter.js";

const router = Router();


router.use("/user",userRoute);
router.use("/client", clientRouter)
router.use("/landing-page", landingPageApiRouter)
router.use("/transaction", transactionApiRouter)
router.get("/blacklist", getAllBlacklistedTokens);

router.post("/login", authApiController.login);
router.post("/2fa/verify" ,authApiController.verify2FA);
router.post("/logout",isAuthenticated ,authApiController.logout); 






export default router;

