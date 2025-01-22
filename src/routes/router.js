import { Router } from "express";
import apiRouter from './apiRoutes/apiRoutes.js'

const router = Router();

router.use("/api", apiRouter);


export default router