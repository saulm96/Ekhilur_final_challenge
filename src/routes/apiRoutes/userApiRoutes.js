import {Router} from "express";
import userApiController from "../../controllers/userController/userApiController.js"

import {isAutenticated} from "../../middlewares/authMiddleware.js";



const router = Router();

router.get("/:email", userApiController.getUserByEmail);



export default router;
