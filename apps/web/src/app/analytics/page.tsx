"use client";

import { useState } from "react";
import { DiseaseProgressionChart } from "../../components/analytics/DiseaseProgressionChart";
import { ReadmissionRiskGauge } from "../../components/analytics/ReadmissionRiskGauge";
import { TreatmentComparisonChart } from "../../components/analytics/TreatmentComparisonChart";

// Mock Data
const MOCK_TIME_SERIES = Array.from({ length: 12 }, (_, i) => ({
  date: `2024-${i + 1}-01`,
  value: 40 + Math.random() * 20 + i * 2,
  ciLow: 30 + i * 2,
  ciHigh: 60 + i * 2,
  populationAvg: 50,
}));

const MOCK_TREATMENTS = [
  {
    name: "Medication A",
    effectiveness: 85,
    sideEffectRisk: 12,
    costScore: 40,
  },
  {
    name: "Medication B",
    effectiveness: 92,
    sideEffectRisk: 25,
    costScore: 80,
  },
  {
    name: "Lifestyle Change",
    effectiveness: 60,
    sideEffectRisk: 0,
    costScore: 10,
  },
];

const MOCK_RISK_FACTORS = [
  { name: "Recent ER Visit", impact: "+15%" },
  { name: "Non-adherence", impact: "+10%" },
  { name: "Comorbidities", impact: "+8%" },
];

export default function AnalyticsPage() {
  const [filter, setFilter] = useState("all");

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
          Predictive Analytics Dashboard
        </h1>
        <p className="text-zinc-500 dark:text-zinc-400">
          AI-driven insights for patient cohorts and outcomes.
        </p>

        {/* Simple Filter */}
        <div className="mt-4 flex space-x-2">
          {["all", "diabetes", "cardiology", "oncology"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-full text-sm capitalize ${
                filter === f
                  ? "bg-blue-600 text-white"
                  : "bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-600"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* Row 1: Key Metrics */}
        <div className="lg:col-span-2">
          <DiseaseProgressionChart
            data={MOCK_TIME_SERIES}
            title="Disease Progression Trajectory (HbA1c)"
          />
        </div>

        <div>
          <ReadmissionRiskGauge riskScore={68} factors={MOCK_RISK_FACTORS} />
        </div>

        {/* Row 2: Deep Dives */}
        <div className="lg:col-span-1">
          <TreatmentComparisonChart options={MOCK_TREATMENTS} />
        </div>

        <div className="lg:col-span-2 bg-white dark:bg-zinc-900 p-4 rounded-xl border border-zinc-200 dark:border-zinc-800">
          <h3 className="text-lg font-semibold mb-4 text-zinc-900 dark:text-zinc-100">
            Population Health Map
          </h3>
          <div className="h-[300px] w-full flex items-center justify-center bg-zinc-100 dark:bg-zinc-800 rounded-lg border-2 border-dashed border-zinc-300 dark:border-zinc-700">
            <span className="text-zinc-400">
              Geographic Heatmap Placeholder (D3 Map)
            </span>
          </div>
          <div className="mt-4 flex justify-between text-sm text-zinc-500">
            <span>Total Patients: 12,450</span>
            <span>High Risk Regions: 3</span>
          </div>
        </div>
      </div>
    </div>
  );
}
