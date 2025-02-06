import {Router} from "express";
import transactionApiController from "../../controllers/transactionController/transactionApiController.js"

const router = Router();    

router.get("/data", transactionApiController.getTransictionPageData);

export default router;