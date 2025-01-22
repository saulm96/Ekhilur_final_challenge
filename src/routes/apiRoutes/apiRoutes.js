import {Router} from 'express';
import userRoute from "./userApiRoutes.js";
const router = Router();

router.use("/user", userRoute);

export default router;

