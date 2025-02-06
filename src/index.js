import express from 'express';
import dotenv from 'dotenv';
import cookieParser from 'cookie-parser';
import cors from 'cors';
import router from '../src/routes/router.js'
import {errorHandler} from "./middlewares/errorMiddleware.js"

dotenv.config();

const app = express();
 const originUrl = process.env.CORS_ORIGIN
const corsOptions = {
    origin: originUrl,
    credentials: true,
    allowHeaders:['Content-Type', 'Authorization']
}

app.use(cors(corsOptions));
app.use(cookieParser());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static("src/public"));
app.use(errorHandler);

app.use('/', router);

app.listen(3000, () => {
    console.log(`Server started on port ${process.env.APP_PORT}`);
});



