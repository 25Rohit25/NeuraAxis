import dotenv from "dotenv";
import express from "express";
import { createServer } from "http";
import { Server } from "socket.io";
import { connectRedis, getRedisAdapter } from "./config/redis";
import { registerSocketHandlers } from "./handlers/socketHandler";
import { authMiddleware } from "./middleware/auth";

dotenv.config();

const app = express();
const httpServer = createServer(app);
const PORT = process.env.PORT || 4000;

async function bootstrap() {
  // 1. Redis Connection
  await connectRedis();

  // 2. Socket.io Setup
  const io = new Server(httpServer, {
    cors: {
      origin: "*", // Lock this down in prod
      methods: ["GET", "POST"],
    },
    adapter: getRedisAdapter(),
  });

  // 3. Middleware
  io.use(authMiddleware);

  // 4. Handlers
  io.on("connection", (socket) => {
    registerSocketHandlers(io, socket as any);
  });

  // 5. Health Check
  app.get("/health", (req, res) => {
    res.send({ status: "ok", service: "realtime-service" });
  });

  // Start
  httpServer.listen(PORT, () => {
    console.log(`Realtime service listening on port ${PORT}`);
  });
}

bootstrap().catch((err) => {
  console.error("Failed to start server:", err);
});
