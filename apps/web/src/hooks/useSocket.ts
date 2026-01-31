import { useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";

const REALTIME_URL =
  process.env.NEXT_PUBLIC_REALTIME_URL || "http://localhost:4000";

interface UseSocketOptions {
  token?: string;
  caseId?: string;
  onMessage?: (msg: any) => void;
  onPresenceUpdate?: (users: any[]) => void;
  onCursorUpdate?: (data: any) => void;
}

export const useSocket = ({
  token,
  caseId,
  onMessage,
  onPresenceUpdate,
  onCursorUpdate,
}: UseSocketOptions) => {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState<any[]>([]);

  useEffect(() => {
    if (!token || !caseId) return;

    // Initialize Socket
    const socket = io(REALTIME_URL, {
      auth: { token },
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    socketRef.current = socket;

    socket.on("connect", () => {
      console.log("Socket Connected");
      setIsConnected(true);
      socket.emit("join-case", caseId);
    });

    socket.on("disconnect", () => {
      console.log("Socket Disconnected");
      setIsConnected(false);
    });

    socket.on("connect_error", (err) => {
      console.error("Socket Connection Error:", err.message);
    });

    // Event Listeners
    socket.on("presence-sync", (users) => {
      setOnlineUsers(users);
      if (onPresenceUpdate) onPresenceUpdate(users);
    });

    socket.on("user-joined", (user) => {
      setOnlineUsers((prev) => [...prev, user]);
    });

    socket.on("user-left", (userId) => {
      setOnlineUsers((prev) => prev.filter((u) => u.id !== userId));
    });

    if (onMessage) {
      socket.on("new-message", onMessage);
    }

    if (onCursorUpdate) {
      socket.on("cursor-update", onCursorUpdate);
    }

    return () => {
      if (caseId) socket.emit("leave-case", caseId);
      socket.disconnect();
    };
  }, [token, caseId]); // Re-run if caseId changes

  const sendMessage = (content: string) => {
    if (socketRef.current && caseId) {
      socketRef.current.emit("send-message", { caseId, content });
    }
  };

  const sendCursorMove = (x: number, y: number) => {
    // Rate limit this in production!
    if (socketRef.current && caseId) {
      socketRef.current.emit("cursor-move", { caseId, x, y });
    }
  };

  return {
    socket: socketRef.current,
    isConnected,
    onlineUsers,
    sendMessage,
    sendCursorMove,
  };
};
