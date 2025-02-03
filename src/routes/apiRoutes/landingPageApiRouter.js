import {Router} from "express";
import landigPageApiController from "../../controllers/landingPageController/landingPageApiController.js"

const router = Router();

router.get("/all", landigPageApiController.getLandingPageData); 


export default router;