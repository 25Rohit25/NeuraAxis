import { Server } from "socket.io";
import { AuthenticatedSocket } from "../middleware/auth";

// Events
interface ClientToServerEvents {
  "join-case": (caseId: string) => void;
  "leave-case": (caseId: string) => void;
  "cursor-move": (data: { caseId: string; x: number; y: number }) => void;
  "send-message": (data: { caseId: string; content: string }) => void;
  "typing-start": (caseId: string) => void;
  "typing-stop": (caseId: string) => void;
}

interface ServerToClientEvents {
  "user-joined": (user: { id: string; name: string }) => void;
  "user-left": (userId: string) => void;
  "cursor-update": (data: {
    userId: string;
    x: number;
    y: number;
    name: string;
  }) => void;
  "new-message": (message: {
    id: string;
    userId: string;
    name: string;
    content: string;
    timestamp: Date;
  }) => void;
  "user-typing": (data: { userId: string; isTyping: boolean }) => void;
  "presence-sync": (users: Array<{ id: string; name: string }>) => void;
  "case-updated": (data: any) => void;
}

// Handler
export const registerSocketHandlers = (
  io: Server<ClientToServerEvents, ServerToClientEvents>,
  socket: AuthenticatedSocket
) => {
  const user = socket.user!;

  console.log(`User connected: ${user.name} (${user.id})`);

  // Handle Join Case (Room)
  socket.on("join-case", async (caseId: string) => {
    await socket.join(caseId);
    console.log(`User ${user.id} joined case ${caseId}`);

    // Broadcast to others in the room
    socket.to(caseId).emit("user-joined", { id: user.id, name: user.name });

    // Sync Presence (get all users in room)
    const sockets = await io.in(caseId).fetchSockets();
    const activeUsers = sockets.map((s) => {
      const u = (s as unknown as AuthenticatedSocket).user;
      return { id: u?.id || "unknown", name: u?.name || "Anonymous" };
    });

    // Send full list to the joiner
    socket.emit("presence-sync", activeUsers);
  });

  // Handle Leave Case
  socket.on("leave-case", (caseId: string) => {
    socket.leave(caseId);
    socket.to(caseId).emit("user-left", user.id);
  });

  // Handle Cursor Movement (Volatile for performance)
  socket.on("cursor-move", (data) => {
    // Determine room? Or pass strictly caseId
    if (data.caseId) {
      socket.to(data.caseId).emit("cursor-update", {
        userId: user.id,
        name: user.name,
        x: data.x,
        y: data.y,
      });
    }
  });

  // Handle Chat Message
  socket.on("send-message", (data) => {
    const msg = {
      id: Date.now().toString(), // Simple ID generation
      userId: user.id,
      name: user.name,
      content: data.content, // TODO: Sanitize here!
      timestamp: new Date(),
    };

    // Broadcast to room (including sender usually, or handle optimistic UI)
    io.to(data.caseId).emit("new-message", msg);
  });

  // Typing Indicators
  socket.on("typing-start", (caseId) => {
    socket.to(caseId).emit("user-typing", { userId: user.id, isTyping: true });
  });

  socket.on("typing-stop", (caseId) => {
    socket.to(caseId).emit("user-typing", { userId: user.id, isTyping: false });
  });

  // Disconnect
  socket.on("disconnecting", () => {
    // Notify all rooms this user is leaving
    for (const room of socket.rooms) {
      socket.to(room).emit("user-left", user.id);
    }
  });
};
