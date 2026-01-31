import { Database } from "@hocuspocus/extension-database";
import { Logger } from "@hocuspocus/extension-logger";
import { Server } from "@hocuspocus/server";
import dotenv from "dotenv";

dotenv.config();

// Simple in-memory storage simulation if no DB logic provided
// In prod, use Postgres/MongoDB via Database extension
const store: Record<string, Uint8Array> = {};

const server = Server.configure({
  port: parseInt(process.env.HOCUSPOCUS_PORT || "1234"),

  extensions: [
    new Logger(),
    // new Redis({
    //   host: process.env.REDIS_HOST || '127.0.0.1',
    //   port: parseInt(process.env.REDIS_PORT || '6379'),
    // })
    new Database({
      fetch: async ({ documentName }) => {
        return new Promise((resolve) => {
          // Simulate DB fetch
          resolve(store[documentName] || null);
        });
      },
      store: async ({ documentName, state }) => {
        store[documentName] = state;
      },
    }),
  ],

  async onAuthenticate(data) {
    const { token } = data;
    // Validate token similarly to main server
    // returning logic
    if (token !== "valid-token") {
      // throw new Error('Not authorized')
    }
  },
});

server.listen().then(() => {
  console.log(`Collab server listening on port ${1234}`);
});
