import {Router} from "express";
import predictApiController from "../../controllers/predictController/predictApiController.js"

const router = Router();

router.get("/all", predictApiController.getPredictions);
router.get("/data/update", predictApiController.getUpdatedPredictions);

export default router;