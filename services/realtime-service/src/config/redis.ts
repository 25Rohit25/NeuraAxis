import { createAdapter } from "@socket.io/redis-adapter";
import dotenv from "dotenv";
import { createClient } from "redis";

dotenv.config();

const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";

export const pubClient = createClient({ url: REDIS_URL });
export const subClient = pubClient.duplicate();

export async function connectRedis() {
  await Promise.all([pubClient.connect(), subClient.connect()]);
  console.log("Redis connected for Pub/Sub");
}

export function getRedisAdapter() {
  return createAdapter(pubClient, subClient);
}
