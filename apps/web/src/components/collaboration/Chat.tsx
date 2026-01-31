import React, { useState } from "react";
import { useSocket } from "../../hooks/useSocket";

interface ChatProps {
  caseId: string;
  token: string;
  currentUser: { id: string; name: string };
}

interface Message {
  id: string;
  userId: string;
  name: string;
  content: string;
  timestamp: string;
}

export const CollaborationChat: React.FC<ChatProps> = ({
  caseId,
  token,
  currentUser,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");

  const { sendMessage, isConnected, onlineUsers } = useSocket({
    token,
    caseId,
    onMessage: (msg: Message) => {
      setMessages((prev) => [...prev, msg]);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;
    sendMessage(inputValue);
    setInputValue("");
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-zinc-900 border-l border-zinc-200 dark:border-zinc-800 w-80">
      {/* Header */}
      <div className="p-4 border-b border-zinc-200 dark:border-zinc-800 flex justify-between items-center">
        <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
          Live Chat
        </h3>
        <div className="flex items-center space-x-2">
          <div
            className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`}
          />
          <span className="text-xs text-zinc-500">
            {onlineUsers.length} online
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => {
          const isMe = msg.userId === currentUser.id;
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isMe ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-2 text-sm ${
                  isMe
                    ? "bg-blue-600 text-white rounded-br-none"
                    : "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-bl-none"
                }`}
              >
                {!isMe && (
                  <span className="text-xs opacity-50 block mb-1">
                    {msg.name}
                  </span>
                )}
                {msg.content}
              </div>
              <span className="text-[10px] text-zinc-400 mt-1">
                {new Date(msg.timestamp).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          );
        })}
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="p-4 border-t border-zinc-200 dark:border-zinc-800"
      >
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 bg-zinc-100 dark:bg-zinc-800 border-none rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 text-zinc-900 dark:text-white"
          />
          <button
            type="submit"
            disabled={!isConnected}
            className="bg-blue-600 text-white rounded-md px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
};
