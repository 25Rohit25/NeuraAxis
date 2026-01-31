import jwt from "jsonwebtoken";
import { Socket } from "socket.io";

const JWT_SECRET = process.env.JWT_SECRET || "super_secret_key";

export interface AuthenticatedSocket extends Socket {
  user?: {
    id: string;
    email: string;
    role: string;
    name: string;
  };
}

export const authMiddleware = (socket: Socket, next: (err?: Error) => void) => {
  const token =
    socket.handshake.auth.token ||
    socket.handshake.headers.authorization?.split(" ")[1];

  if (!token) {
    return next(new Error("Authentication error: Token missing"));
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET) as any;
    (socket as AuthenticatedSocket).user = decoded;
    next();
  } catch (err) {
    next(new Error("Authentication error: Invalid token"));
  }
};
