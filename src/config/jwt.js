import jwt from 'jsonwebtoken';
import dotenv from 'dotenv';

dotenv.config();
const SECRET = process.env.JWT_SECRET;

function sign(data, expiresIn = '1d') {
  const token = jwt.sign(data, SECRET, { expiresIn });
  return token;
  }
  
  function verify(token) {
    try {
        const response = jwt.verify(token, SECRET);
        return response;
    } catch (error) {
        console.log(error)
        return{ error: error.message, status: 500};
    }
}

export default {
  sign,
  verify,
};

