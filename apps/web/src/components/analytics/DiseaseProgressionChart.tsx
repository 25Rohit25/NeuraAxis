import React from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface DataPoint {
  date: string;
  value: number;
  ciLow: number;
  ciHigh: number;
  populationAvg: number;
}

interface Props {
  data: DataPoint[];
  title: string;
}

export const DiseaseProgressionChart: React.FC<Props> = ({ data, title }) => {
  return (
    <div className="bg-white dark:bg-zinc-900 p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm">
      <h3 className="text-lg font-semibold mb-4 text-zinc-900 dark:text-zinc-100">
        {title}
      </h3>
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={data}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                borderRadius: "8px",
                border: "none",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
              }}
            />
            <Legend />

            {/* Confidence Interval using Area (trick: stack or range) */}
            {/* Recharts Area doesn't natively support [min,max] range well without tricks.
                Standard workaround: Stacked Area where bottom is transparent?
                Or simply plot two lines and fill between?
                Simpler approach for prototype: Just plot the Area for CI if data is formatted as [min, max]
            */}

            <Area
              type="monotone"
              dataKey="ciHigh"
              stroke="none"
              fill="#3b82f6"
              fillOpacity={0.1}
            />
            {/* This is a simplification. For true CI band, usually D3 is better or Recharts 'range' feature if available in specific version. */}

            <Line
              type="monotone"
              dataKey="value"
              stroke="#2563eb"
              strokeWidth={3}
              dot={{ r: 4 }}
              name="Patient Value"
            />

            <Line
              type="monotone"
              dataKey="populationAvg"
              stroke="#9ca3af"
              strokeDasharray="5 5"
              strokeWidth={2}
              dot={false}
              name="Population Avg"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
