import React from "react";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

interface Props {
  riskScore: number; // 0-100
  factors: Array<{ name: string; impact: string }>;
}

export const ReadmissionRiskGauge: React.FC<Props> = ({
  riskScore,
  factors,
}) => {
  // Gauge Data: Value vs Remainder
  const data = [
    { name: "Risk", value: riskScore },
    { name: "Remaining", value: 100 - riskScore },
  ];

  // Determine Color based on Risk
  let color = "#22c55e"; // Green
  if (riskScore > 30) color = "#eab308"; // Yellow
  if (riskScore > 70) color = "#ef4444"; // Red

  return (
    <div className="bg-white dark:bg-zinc-900 p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm flex flex-col items-center">
      <h3 className="text-lg font-semibold mb-2 text-zinc-900 dark:text-zinc-100 self-start">
        Readmission Risk
      </h3>

      <div className="h-[200px] w-full relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="100%" // Half circle via centering at bottom
              startAngle={180}
              endAngle={0}
              innerRadius={80}
              outerRadius={120}
              paddingAngle={0}
              dataKey="value"
            >
              <Cell fill={color} />
              <Cell fill="#e4e4e7" /> {/* grey-200 */}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute bottom-0 left-0 right-0 flex flex-col items-center justify-center -mb-4">
          <span className="text-4xl font-bold text-zinc-900 dark:text-zinc-100">
            {riskScore}%
          </span>
          <span className="text-sm text-zinc-500">Probability</span>
        </div>
      </div>

      <div className="w-full mt-8">
        <h4 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-2">
          Key Drivers
        </h4>
        <ul className="space-y-2">
          {factors.map((f, i) => (
            <li key={i} className="flex justify-between text-sm">
              <span className="text-zinc-700 dark:text-zinc-300">{f.name}</span>
              <span className="font-medium text-red-500">{f.impact}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
