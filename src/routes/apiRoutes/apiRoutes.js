import {Router} from 'express';

import authApiController from "../../controllers/authController/authApiController.js";

import userRoute from "./userApiRoutes.js";

const router = Router();



router.post("/login", authApiController.login);
router.use("/user", userRoute);




export default router;

