import React from "react";

// Reuse type interface if possible
interface Alert {
  rule_id: string;
  rule_name: string;
  message: string;
  suggestion?: string;
  category: string;
}

interface Props {
  alerts: Alert[];
  onDismiss: (id: string) => void;
}

export const WarningBanner: React.FC<Props> = ({ alerts, onDismiss }) => {
  if (alerts.length === 0) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-40 flex flex-col items-center pointer-events-none">
      {/* Use pointer-events-auto on the banners themselves */}
      <div className="flex flex-col space-y-2 mt-4 w-full max-w-4xl px-4 pointer-events-auto">
        {alerts.map((alert) => (
          <div
            key={alert.rule_id}
            className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 text-yellow-800 dark:text-yellow-100 px-4 py-3 rounded-lg shadow-md flex items-start justify-between animate-in slide-in-from-top-2 duration-300"
          >
            <div className="flex items-start space-x-3">
              <svg
                className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0"
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
              <div>
                <strong className="font-semibold">{alert.rule_name}</strong>
                <p className="text-sm mt-1">{alert.message}</p>
                {alert.suggestion && (
                  <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1 italic">
                    Suggestion: {alert.suggestion}
                  </p>
                )}
              </div>
            </div>

            <button
              onClick={() => onDismiss(alert.rule_id)}
              className="text-yellow-500 hover:text-yellow-700 p-1 ml-4"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
