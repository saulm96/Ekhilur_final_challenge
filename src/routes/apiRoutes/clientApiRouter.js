import {Router} from "express";
import clientApiController from "../../controllers/clientController/clientApiController.js"

const router = Router();

router.get("/all", clientApiController.getAllClients);
router.get("/data", clientApiController.getClientPageData);


export default router;



