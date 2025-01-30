import {Router} from 'express';
import { isAuthenticated } from "../../middlewares/authMiddleware.js";
import { getAllBlacklistedTokens } from "../../controllers/adminInfoController/adminInfoApiController.js";
import authApiController from "../../controllers/authController/authApiController.js";
import {isAdmin, isCouncil} from "../../middlewares/rolesMiddleware.js";



import userRoute from "./userApiRoutes.js";
import clientRouter from "./clientApiRouter.js";

const router = Router();


router.use("/user",userRoute);
router.use("/client" ,clientRouter)
router.get("/blacklist", isAdmin ,getAllBlacklistedTokens);  //Para roles de admin

router.post("/login", authApiController.login);
router.post("/2fa/verify" ,authApiController.verify2FA);
router.post("/logout",isAuthenticated ,authApiController.logout); 

//Endpoints para que los de ciberseguridad prueben si son capaces de escalar en privilegios 







export default router;

