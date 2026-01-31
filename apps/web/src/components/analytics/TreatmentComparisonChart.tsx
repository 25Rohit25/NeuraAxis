import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface TreatmentOption {
  name: string;
  effectiveness: number; // 0-100
  sideEffectRisk: number; // 0-100
  costScore: number; // Normalized 0-100 for viz
}

interface Props {
  options: TreatmentOption[];
}

export const TreatmentComparisonChart: React.FC<Props> = ({ options }) => {
  return (
    <div className="bg-white dark:bg-zinc-900 p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm">
      <h3 className="text-lg font-semibold mb-4 text-zinc-900 dark:text-zinc-100">
        Treatment Options Analysis
      </h3>
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={options}
            layout="vertical"
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              horizontal={false}
              opacity={0.3}
            />
            <XAxis type="number" domain={[0, 100]} />
            <YAxis dataKey="name" type="category" width={100} />
            <Tooltip cursor={{ fill: "transparent" }} />
            <Legend />
            <Bar
              dataKey="effectiveness"
              name="Effectiveness %"
              fill="#22c55e"
              radius={[0, 4, 4, 0]}
              barSize={20}
            />
            <Bar
              dataKey="sideEffectRisk"
              name="Side Effect Risk %"
              fill="#ef4444"
              radius={[0, 4, 4, 0]}
              barSize={20}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-zinc-500 mt-2 italic">
        * Predictions based on patient biomarkers and historical data.
      </p>
    </div>
  );
};
