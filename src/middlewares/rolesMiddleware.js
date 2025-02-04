async function isAdmin(req, res, next) {
    const authorization = req.headers.authorization;
    if (!authorization) return res.status(401).json({ message: 'no token provided' });

    const token = authorization.replace("Bearer ", "");
    const verified = jwt.verify(token);

    if (verified.error) return res.status(401).json({ message: 'incorrect jwt token' });

    if (verified.role !== 'admin' || !verified.role) return res.status(403).json({ message: 'you are not an admin' });

    next();
}

async function isCouncil(req, res, next) {
    const authorization = req.headers.authorization;
    if (!authorization) return res.status(401).json({ message: 'no token provided' });

    const token = authorization.replace("Bearer ", "");
    const verified = jwt.verify(token);

    if (verified.error) return res.status(401).json({ message: 'incorrect jwt token' });

    if (verified.role !== 'council' || !verified.role) return res.status(403).json({ message: 'you are not a council' });

    next();
}

export { isAdmin, isCouncil };
