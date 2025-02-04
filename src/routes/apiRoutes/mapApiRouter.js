import {Router} from "express";
import clientMapApiController from "../../controllers/clientMapController/clientMapApiController.js"
import ticketMapApiController  from "../../controllers/ticketMapController/ticketMapApiController.js";

const router = Router();

router.get("/clients", clientMapApiController.getClientMap);
router.get("/tickets", ticketMapApiController.getTicketMap);

export default router;