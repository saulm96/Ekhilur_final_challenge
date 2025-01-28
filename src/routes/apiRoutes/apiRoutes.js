import {Router} from 'express';
import { isAuthenticated } from "../../middlewares/authMiddleware.js";
import authApiController from "../../controllers/authController/authApiController.js";

import userRoute from "./userApiRoutes.js";

const router = Router();



router.post("/login", authApiController.login);
router.post("/logout",isAuthenticated ,authApiController.logout); 


router.use("/user", isAuthenticated ,userRoute);




export default router;

