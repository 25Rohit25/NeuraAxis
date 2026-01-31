import React, { useState } from "react";

export interface Alert {
  rule_id: string;
  rule_name: string;
  category: string;
  priority: number;
  message: string;
  suggestion?: string;
  evidence_link?: string;
}

interface Props {
  alert: Alert | null;
  onAcknowledge: (alertId: string) => void;
  onOverride: (alertId: string, reason: string) => void;
}

export const CriticalAlertModal: React.FC<Props> = ({
  alert,
  onAcknowledge,
  onOverride,
}) => {
  const [isOverriding, setIsOverriding] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");

  if (!alert) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-zinc-900 border-2 border-red-500 rounded-xl shadow-2xl max-w-lg w-full overflow-hidden animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-red-500 p-4 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <h2 className="text-xl font-bold">Critical Clinical Alert</h2>
          </div>
          <span className="text-xs uppercase bg-red-700 px-2 py-1 rounded">
            {alert.category}
          </span>
        </div>

        {/* content */}
        <div className="p-6">
          <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 text-lg mb-2">
            {alert.rule_name}
          </h3>
          <p className="text-zinc-700 dark:text-zinc-300 text-base leading-relaxed mb-4">
            {alert.message}
          </p>

          {alert.suggestion && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-3 rounded-lg mb-4">
              <span className="font-semibold text-blue-800 dark:text-blue-300 block text-xs uppercase mb-1">
                Recommendation
              </span>
              <p className="text-blue-900 dark:text-blue-100 text-sm">
                {alert.suggestion}
              </p>
            </div>
          )}

          {alert.evidence_link && (
            <a
              href={alert.evidence_link}
              target="_blank"
              rel="noopener"
              className="text-xs text-blue-600 hover:underline mb-4 block"
            >
              View Clinical Guidelines
            </a>
          )}

          {isOverriding && (
            <div className="mt-4">
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Reason for Override <span className="text-red-500">*</span>
              </label>
              <textarea
                className="w-full border border-zinc-300 dark:border-zinc-700 rounded-md p-2 text-sm bg-white dark:bg-zinc-800 focus:ring-2 focus:ring-red-500 outline-none"
                rows={3}
                placeholder="Document why you are proceeding despite the alert..."
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-zinc-50 dark:bg-zinc-950 p-4 flex justify-between items-center border-t border-zinc-200 dark:border-zinc-800">
          {!isOverriding ? (
            <>
              <button
                onClick={() => setIsOverriding(true)}
                className="text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 text-sm font-medium px-4 py-2"
              >
                Override Alert
              </button>
              <button
                onClick={() => onAcknowledge(alert.rule_id)}
                className="bg-red-600 hover:bg-red-700 text-white font-medium px-6 py-2 rounded-lg shadow-lg"
              >
                Acknowledge & Address
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setIsOverriding(false)}
                className="text-zinc-500 hover:text-zinc-800 text-sm font-medium px-4 py-2"
              >
                Cancel Override
              </button>
              <button
                onClick={() => {
                  if (overrideReason.trim().length > 5) {
                    onOverride(alert.rule_id, overrideReason);
                  }
                }}
                disabled={overrideReason.trim().length < 5}
                className="bg-zinc-800 hover:bg-zinc-900 text-white font-medium px-6 py-2 rounded-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Confirm Override
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
