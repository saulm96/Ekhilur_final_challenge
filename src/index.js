import express from 'express';
import dotenv from 'dotenv';
import cors from 'cors';
import router from '../src/routes/router.js'

dotenv.config();

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static("src/public"));

/* app.use(session({
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: true,
    cookie: { secure: false }
})); */

app.use('/', router);

app.listen(3000, () => {
    console.log(`Server started on port ${process.env.APP_PORT}`);
});



