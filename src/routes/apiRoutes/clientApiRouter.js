import {Router} from "express";
import clientApiController from "../../controllers/clientController/clientApiController.js"

const router = Router();

router.get("/data", clientApiController.getClientPageData);
router.get("/data/update", clientApiController.getUpdatedClientPageData)


export default router;



