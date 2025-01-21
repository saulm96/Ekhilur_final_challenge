import { Router } from "express";
import apiRouter from './apiRoutes/apiRoutes.js'

const router = Router();

router.use("/api/v1", apiRouter);

export default router;