export default function checkIfTheTokenExistsAndTheType(authorization){
    if(!authorization){
        console.log('no authorization header')
        return res.status(401).json({ message: 'No authorization header' });
    }
    if(!authorization.startsWith('Bearer ')){
        console.log('invalid authorization header')
        return res.status(401).json({ message: 'Invalid authorization header' });
    }

    return authorization;
}