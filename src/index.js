import express from 'express';
import dotenv from 'dotenv';
import cookieParser from 'cookie-parser';
import cors from 'cors';
import router from '../src/routes/router.js'
import {errorHandler} from "./middlewares/errorMiddleware.js"

dotenv.config();

const app = express();

const corsOptions = {
    origin: process.env.CORS_ORIGIN,
    credentials: true,
    optionSuccessStatus: 200
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



