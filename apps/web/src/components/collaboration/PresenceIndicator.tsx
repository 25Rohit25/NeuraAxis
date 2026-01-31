import React from "react";

interface User {
  id: string;
  name: string;
  color?: string; // Optional avatar color
}

interface PresenceProps {
  users: User[];
  currentUserId: string;
}

export const PresenceIndicator: React.FC<PresenceProps> = ({
  users,
  currentUserId,
}) => {
  // Filter out current user usually, or show all
  const others = users.filter((u) => u.id !== currentUserId);
  const displayLimit = 3;

  return (
    <div className="flex -space-x-2 overflow-hidden items-center">
      {/* Current User (Usually separate or first) */}

      {others.slice(0, displayLimit).map((user) => (
        <div
          key={user.id}
          className="inline-block h-8 w-8 rounded-full ring-2 ring-white dark:ring-zinc-900 bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center text-xs font-medium text-white shadow-sm tooltip"
          title={user.name}
        >
          {user.name.charAt(0).toUpperCase()}
        </div>
      ))}

      {others.length > displayLimit && (
        <div className="inline-block h-8 w-8 rounded-full ring-2 ring-white dark:ring-zinc-900 bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center text-xs font-medium text-zinc-600 dark:text-zinc-300">
          +{others.length - displayLimit}
        </div>
      )}

      {others.length === 0 && (
        <span className="text-xs text-zinc-500 ml-3">No other viewers</span>
      )}
    </div>
  );
};
