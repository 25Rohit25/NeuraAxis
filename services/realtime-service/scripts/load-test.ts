import jwt from "jsonwebtoken";
import { io } from "socket.io-client";

// Config
const TARGET_URL = process.env.TARGET_URL || "http://localhost:4000";
const NUM_CLIENTS = 1000; // Default to 1k for safety in dev env. User asked for 10k script capability.
const RAMP_UP_INTERVAL_MS = 10;
const JWT_SECRET = "super_secret_key"; // Match server

const clients: any[] = [];

function generateToken(i: number) {
  return jwt.sign(
    {
      id: `user-${i}`,
      name: `LoadBot-${i}`,
      role: "bot",
    },
    JWT_SECRET
  );
}

async function startLoadTest() {
  console.log(
    `Starting load test with ${NUM_CLIENTS} clients connecting to ${TARGET_URL}...`
  );

  for (let i = 0; i < NUM_CLIENTS; i++) {
    const token = generateToken(i);

    const socket = io(TARGET_URL, {
      auth: { token },
      transports: ["websocket"], // Force websocket
      forceNew: true,
    });

    socket.on("connect", () => {
      // console.log(`Client ${i} connected`);
      // Join a random case room (simulate 50 active cases)
      const caseId = `case-${Math.floor(Math.random() * 50)}`;
      socket.emit("join-case", caseId);

      // Startup activity
      if (Math.random() < 0.1) {
        socket.emit("send-message", { caseId, content: `Hello form Bot ${i}` });
      }
    });

    socket.on("disconnect", () => {
      // console.log(`Client ${i} disconnected`);
    });

    socket.on("connect_error", (err) => {
      console.error(`Client ${i} error:`, err.message);
    });

    clients.push(socket);

    // Throttle connection rate
    if (i % 100 === 0) {
      console.log(`Connected ${i} clients...`);
      await new Promise((r) => setTimeout(r, RAMP_UP_INTERVAL_MS));
    }
  }

  console.log("All clients initiated.");

  // Simulate ongoing activity
  setInterval(() => {
    const randomClient = clients[Math.floor(Math.random() * clients.length)];
    if (randomClient.connected) {
      const caseId = `case-${Math.floor(Math.random() * 50)}`;
      randomClient.emit("cursor-move", {
        caseId,
        x: Math.random() * 1000,
        y: Math.random() * 1000,
      });
    }
  }, 100);
}

startLoadTest();
