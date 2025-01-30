import bcryptjs from 'bcryptjs';

async function hashPassword(password){
    const hash = await bcryptjs.hash(password, 10);
    return hash
}

async function verifyPassword(password, hashedPassword){
    const match = await bcryptjs.compare(password, hashedPassword);
    return match
}
const hashed = bcryptjs.hashSync("G7v!zKp4Xq", 10);
console.log(hashed);

export {hashPassword, verifyPassword};
