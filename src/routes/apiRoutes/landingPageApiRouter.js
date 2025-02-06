import {Router} from "express";
import landigPageApiController, { landingPageApiController } from "../../controllers/landingPageController/landingPageApiController.js"

const router = Router();

router.get("/all", landigPageApiController.getLandingPageData); 
router.get("/data/update", landingPageApiController.getUpdatedLandingPage)


export default router;