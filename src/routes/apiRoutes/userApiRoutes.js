import {Router} from "express";
import userApiController from "../../controllers/userController/userApiController.js"

const router = Router();

router.get("/list", userApiController.getAllUsers);
router.get("/:id", userApiController.getUserById);

export default router;