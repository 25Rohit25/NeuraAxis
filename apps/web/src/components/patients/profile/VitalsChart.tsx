/**
 * NEURAXIS - Vitals Chart Component
 * Interactive vitals visualization with Recharts
 */

"use client";

import { cn, formatDate } from "@/lib/utils";
import type { VitalTrend, VitalType } from "@/types/patient-profile";
import React, { useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface VitalsChartProps {
  vitalTrends: VitalTrend[];
  isLoading?: boolean;
  className?: string;
}

const VITAL_CONFIG: Record<
  VitalType,
  { label: string; color: string; icon: React.ReactNode }
> = {
  blood_pressure: {
    label: "Blood Pressure",
    color: "#ef4444",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
      </svg>
    ),
  },
  heart_rate: {
    label: "Heart Rate",
    color: "#f97316",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
      </svg>
    ),
  },
  temperature: {
    label: "Temperature",
    color: "#eab308",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z" />
      </svg>
    ),
  },
  respiratory_rate: {
    label: "Respiratory Rate",
    color: "#22c55e",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z" />
        <path d="M12 6v6l4 2" />
      </svg>
    ),
  },
  oxygen_saturation: {
    label: "SpO₂",
    color: "#3b82f6",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <circle cx="12" cy="12" r="10" />
        <path d="M12 2a10 10 0 0 1 0 20" />
      </svg>
    ),
  },
  weight: {
    label: "Weight",
    color: "#8b5cf6",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M12 3v18" />
        <path d="m5 6 7-3 7 3" />
        <path d="M5 18h14" />
      </svg>
    ),
  },
  height: {
    label: "Height",
    color: "#06b6d4",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M12 22V2" />
        <path d="m5 12 7-10 7 10" />
      </svg>
    ),
  },
  bmi: {
    label: "BMI",
    color: "#ec4899",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <path d="M9 9h6v6H9z" />
      </svg>
    ),
  },
};

export function VitalsChart({
  vitalTrends,
  isLoading,
  className,
}: VitalsChartProps) {
  const [selectedVital, setSelectedVital] =
    useState<VitalType>("blood_pressure");
  const [timeRange, setTimeRange] = useState<"7d" | "30d" | "90d" | "1y">(
    "30d"
  );

  const currentTrend = vitalTrends.find((t) => t.type === selectedVital);
  const config = VITAL_CONFIG[selectedVital];

  // Filter data by time range
  const filterDataByRange = (readings: VitalTrend["readings"]) => {
    const now = new Date();
    const cutoff = new Date();
    if (timeRange === "7d") cutoff.setDate(now.getDate() - 7);
    if (timeRange === "30d") cutoff.setDate(now.getDate() - 30);
    if (timeRange === "90d") cutoff.setDate(now.getDate() - 90);
    if (timeRange === "1y") cutoff.setFullYear(now.getFullYear() - 1);

    return readings.filter((r) => new Date(r.date) >= cutoff);
  };

  const chartData = currentTrend
    ? filterDataByRange(currentTrend.readings)
    : [];

  const getTrendIcon = (trend: "up" | "down" | "stable") => {
    if (trend === "up") {
      return (
        <svg
          className="h-4 w-4 text-success"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
          <polyline points="17 6 23 6 23 12" />
        </svg>
      );
    }
    if (trend === "down") {
      return (
        <svg
          className="h-4 w-4 text-danger"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
          <polyline points="17 18 23 18 23 12" />
        </svg>
      );
    }
    return (
      <svg
        className="h-4 w-4 text-muted-foreground"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <line x1="5" y1="12" x2="19" y2="12" />
      </svg>
    );
  };

  if (isLoading) {
    return (
      <div className={cn("p-6 rounded-lg border bg-card", className)}>
        <div className="h-[300px] flex items-center justify-center">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" />
        </div>
      </div>
    );
  }

  return (
    <div className={cn("p-6 rounded-lg border bg-card", className)}>
      {/* Vital type selector */}
      <div className="flex flex-wrap gap-2 mb-6">
        {vitalTrends.map((trend) => {
          const vitConfig = VITAL_CONFIG[trend.type];
          return (
            <button
              key={trend.type}
              onClick={() => setSelectedVital(trend.type)}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors",
                selectedVital === trend.type
                  ? "border-primary bg-primary/5"
                  : "hover:bg-muted border-input"
              )}
            >
              <span style={{ color: vitConfig.color }}>{vitConfig.icon}</span>
              <div className="text-left">
                <p className="text-xs font-medium">{vitConfig.label}</p>
                <div className="flex items-center gap-1">
                  <span className="text-sm font-bold">
                    {trend.type === "blood_pressure"
                      ? `${trend.readings[trend.readings.length - 1]?.systolic || 0}/${trend.readings[trend.readings.length - 1]?.diastolic || 0}`
                      : trend.latestValue}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {trend.unit}
                  </span>
                  {getTrendIcon(trend.trend)}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Time range selector */}
      <div className="flex gap-2 mb-4">
        {(["7d", "30d", "90d", "1y"] as const).map((range) => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={cn(
              "px-3 py-1 text-xs rounded-full transition-colors",
              timeRange === range
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            )}
          >
            {range === "7d"
              ? "7 Days"
              : range === "30d"
                ? "30 Days"
                : range === "90d"
                  ? "90 Days"
                  : "1 Year"}
          </button>
        ))}
      </div>

      {/* Chart */}
      {chartData.length === 0 ? (
        <div className="h-[250px] flex items-center justify-center text-muted-foreground">
          No data available for this period
        </div>
      ) : (
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            {selectedVital === "blood_pressure" ? (
              <ComposedChart
                data={chartData}
                margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) =>
                    formatDate(value, { month: "short", day: "numeric" })
                  }
                  fontSize={12}
                  stroke="var(--muted-foreground)"
                />
                <YAxis
                  fontSize={12}
                  stroke="var(--muted-foreground)"
                  domain={[60, 180]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                  }}
                  formatter={(value: number, name: string) => [
                    value,
                    name === "systolic" ? "Systolic" : "Diastolic",
                  ]}
                  labelFormatter={(label) => formatDate(label)}
                />
                <ReferenceLine
                  y={120}
                  stroke="#22c55e"
                  strokeDasharray="3 3"
                  label={{ value: "Normal", fontSize: 10 }}
                />
                <ReferenceLine y={80} stroke="#22c55e" strokeDasharray="3 3" />
                <Area
                  type="monotone"
                  dataKey="systolic"
                  fill={`${config.color}20`}
                  stroke={config.color}
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="diastolic"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </ComposedChart>
            ) : (
              <LineChart
                data={chartData}
                margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) =>
                    formatDate(value, { month: "short", day: "numeric" })
                  }
                  fontSize={12}
                  stroke="var(--muted-foreground)"
                />
                <YAxis fontSize={12} stroke="var(--muted-foreground)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                  }}
                  formatter={(value: number) => [
                    `${value} ${currentTrend?.unit}`,
                    config.label,
                  ]}
                  labelFormatter={(label) => formatDate(label)}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={config.color}
                  strokeWidth={2}
                  dot={{ r: 3, fill: config.color }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      )}

      {/* Legend for blood pressure */}
      {selectedVital === "blood_pressure" && (
        <div className="flex justify-center gap-6 mt-4 text-xs">
          <div className="flex items-center gap-2">
            <div
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: config.color }}
            />
            <span>Systolic</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-blue-500" />
            <span>Diastolic</span>
          </div>
          <div className="flex items-center gap-2">
            <div
              className="h-0.5 w-6 bg-success"
              style={{ borderStyle: "dashed" }}
            />
            <span>Normal Range</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default VitalsChart;
