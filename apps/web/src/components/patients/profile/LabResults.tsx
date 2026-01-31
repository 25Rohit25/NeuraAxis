/**
 * NEURAXIS - Lab Results Component
 * Display lab test results with normal range indicators
 */

"use client";

import { Modal } from "@/components/ui/Modal";
import { cn, formatDate } from "@/lib/utils";
import type {
  LabResult,
  LabResultStatus,
  LabTest,
} from "@/types/patient-profile";
import { useState } from "react";

interface LabResultsProps {
  labTests: LabTest[];
  isLoading?: boolean;
  className?: string;
}

const STATUS_STYLES: Record<
  LabResultStatus,
  { bg: string; text: string; label: string }
> = {
  normal: { bg: "bg-success/10", text: "text-success", label: "Normal" },
  abnormal_low: { bg: "bg-info/10", text: "text-info", label: "Low" },
  abnormal_high: { bg: "bg-warning/10", text: "text-warning", label: "High" },
  critical: { bg: "bg-danger/10", text: "text-danger", label: "Critical" },
};

export function LabResults({
  labTests,
  isLoading,
  className,
}: LabResultsProps) {
  const [selectedTest, setSelectedTest] = useState<LabTest | null>(null);
  const [filter, setFilter] = useState<"all" | "abnormal">("all");

  // Filter to completed tests with results
  const completedTests = labTests
    .filter((t) => t.status === "completed" && t.results.length > 0)
    .sort(
      (a, b) =>
        new Date(b.resultDate || b.orderDate).getTime() -
        new Date(a.resultDate || a.orderDate).getTime()
    );

  const filteredTests =
    filter === "abnormal"
      ? completedTests.filter((t) =>
          t.results.some((r) => r.status !== "normal")
        )
      : completedTests;

  const getTestStatus = (results: LabResult[]): LabResultStatus => {
    if (results.some((r) => r.status === "critical")) return "critical";
    if (results.some((r) => r.status === "abnormal_high"))
      return "abnormal_high";
    if (results.some((r) => r.status === "abnormal_low")) return "abnormal_low";
    return "normal";
  };

  if (isLoading) {
    return (
      <div className={cn("space-y-3", className)}>
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="p-4 rounded-lg border animate-pulse">
            <div className="h-4 w-1/3 bg-muted rounded mb-2" />
            <div className="h-3 w-2/3 bg-muted rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Header & filter */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M14.5 2v6a2 2 0 0 0 2 2h6" />
            <path d="M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6H6a2 2 0 0 0-2 2v5" />
          </svg>
          Lab Results
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setFilter("all")}
            className={cn(
              "px-3 py-1 text-xs rounded-full transition-colors",
              filter === "all"
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            )}
          >
            All
          </button>
          <button
            onClick={() => setFilter("abnormal")}
            className={cn(
              "px-3 py-1 text-xs rounded-full transition-colors",
              filter === "abnormal"
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            )}
          >
            Abnormal Only
          </button>
        </div>
      </div>

      {/* Pending tests */}
      {labTests.filter((t) => t.status === "pending").length > 0 && (
        <div className="mb-4 p-3 rounded-lg bg-warning/10 border border-warning/20">
          <p className="text-sm font-medium text-warning">
            {labTests.filter((t) => t.status === "pending").length} test(s)
            pending
          </p>
        </div>
      )}

      {/* Results list */}
      {filteredTests.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground bg-muted/30 rounded-lg">
          <svg
            className="h-10 w-10 mx-auto mb-2 opacity-50"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path d="M14.5 2v6a2 2 0 0 0 2 2h6" />
            <path d="M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6H6a2 2 0 0 0-2 2v5" />
          </svg>
          <p>No lab results available</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredTests.map((test) => {
            const overallStatus = getTestStatus(test.results);
            const style = STATUS_STYLES[overallStatus];
            const abnormalCount = test.results.filter(
              (r) => r.status !== "normal"
            ).length;

            return (
              <div
                key={test.id}
                onClick={() => setSelectedTest(test)}
                className={cn(
                  "p-4 rounded-lg border cursor-pointer transition-colors hover:bg-muted/30",
                  overallStatus !== "normal" && style.bg
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-sm">{test.testName}</h4>
                      {abnormalCount > 0 && (
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded text-xs font-medium",
                            style.bg,
                            style.text
                          )}
                        >
                          {abnormalCount} {style.label}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {test.category} •{" "}
                      {formatDate(test.resultDate || test.orderDate)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Ordered by {test.orderedBy.name}
                    </p>
                  </div>

                  {/* Quick values preview */}
                  <div className="text-right shrink-0">
                    <p className="text-xs text-muted-foreground mb-1">
                      {test.results.length} components
                    </p>
                    <svg
                      className="h-4 w-4 ml-auto text-muted-foreground"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Details modal */}
      <Modal
        isOpen={!!selectedTest}
        onClose={() => setSelectedTest(null)}
        title={selectedTest?.testName || ""}
        size="lg"
      >
        {selectedTest && (
          <div className="space-y-4">
            {/* Test info */}
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">Category</p>
                <p>{selectedTest.category}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Test Code</p>
                <p>{selectedTest.testCode || "—"}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Ordered</p>
                <p>{formatDate(selectedTest.orderDate)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Result</p>
                <p>
                  {formatDate(
                    selectedTest.resultDate || selectedTest.orderDate
                  )}
                </p>
              </div>
            </div>

            {/* Results table */}
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium">
                      Component
                    </th>
                    <th className="px-3 py-2 text-right font-medium">Value</th>
                    <th className="px-3 py-2 text-right font-medium">
                      Reference
                    </th>
                    <th className="px-3 py-2 text-center font-medium">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {selectedTest.results.map((result) => {
                    const style = STATUS_STYLES[result.status];
                    return (
                      <tr
                        key={result.id}
                        className={result.status !== "normal" ? style.bg : ""}
                      >
                        <td className="px-3 py-2">
                          <span className="font-medium">
                            {result.component}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right">
                          <span className={cn("font-mono", style.text)}>
                            {result.value} {result.unit}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right text-muted-foreground">
                          {result.referenceRange}
                        </td>
                        <td className="px-3 py-2 text-center">
                          {result.status !== "normal" ? (
                            <span
                              className={cn(
                                "px-2 py-0.5 rounded text-xs font-medium",
                                style.bg,
                                style.text
                              )}
                            >
                              {result.flag || style.label}
                            </span>
                          ) : (
                            <span className="text-success text-xs">✓</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Notes */}
            {selectedTest.results.some((r) => r.notes) && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">
                  Notes
                </p>
                {selectedTest.results
                  .filter((r) => r.notes)
                  .map((r) => (
                    <p key={r.id} className="text-sm mb-1">
                      <span className="font-medium">{r.component}:</span>{" "}
                      {r.notes}
                    </p>
                  ))}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

export default LabResults;
