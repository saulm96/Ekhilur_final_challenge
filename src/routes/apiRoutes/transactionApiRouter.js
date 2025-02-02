import {Router} from "express";
import transactionApiController from "../../controllers/transactionController/transactionApiController.js"

const router = Router();    

router.get("/type", transactionApiController.getSumByTransactionsType);

export default router;