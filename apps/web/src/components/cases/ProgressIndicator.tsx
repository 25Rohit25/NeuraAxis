/**
 * NEURAXIS - Case Creation Progress Indicator
 * Visual step navigation for multi-step form
 */

"use client";

import { useCaseForm } from "@/contexts/CaseFormContext";
import { cn } from "@/lib/utils";
import { CASE_CREATION_STEPS } from "@/types/medical-case";

interface ProgressIndicatorProps {
  className?: string;
  orientation?: "horizontal" | "vertical";
}

export function ProgressIndicator({
  className,
  orientation = "horizontal",
}: ProgressIndicatorProps) {
  const { state, goToStep, isStepComplete } = useCaseForm();

  const steps = CASE_CREATION_STEPS;

  return (
    <nav
      aria-label="Progress"
      className={cn(
        orientation === "horizontal"
          ? "flex items-center justify-between w-full overflow-x-auto pb-2"
          : "flex flex-col space-y-1",
        className
      )}
    >
      {orientation === "horizontal" ? (
        <ol className="flex items-center w-full">
          {steps.map((step, index) => {
            const isComplete = isStepComplete(step.id);
            const isCurrent = state.currentStep === step.id;
            const isClickable = index === 0 || isStepComplete(index - 1);

            return (
              <li
                key={step.id}
                className={cn(
                  "flex items-center",
                  index < steps.length - 1 && "flex-1"
                )}
              >
                <button
                  type="button"
                  onClick={() => isClickable && goToStep(step.id)}
                  disabled={!isClickable}
                  className={cn(
                    "group flex flex-col items-center",
                    isClickable && "cursor-pointer"
                  )}
                >
                  {/* Step circle */}
                  <span
                    className={cn(
                      "flex items-center justify-center w-10 h-10 rounded-full border-2 text-sm font-medium transition-colors",
                      isComplete && !isCurrent
                        ? "bg-success border-success text-white"
                        : isCurrent
                          ? "bg-primary border-primary text-primary-foreground"
                          : "border-muted-foreground/30 text-muted-foreground group-hover:border-primary/50"
                    )}
                  >
                    {isComplete && !isCurrent ? (
                      <svg
                        className="w-5 h-5"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    ) : (
                      step.id + 1
                    )}
                  </span>

                  {/* Step label */}
                  <span
                    className={cn(
                      "mt-2 text-xs font-medium text-center whitespace-nowrap",
                      isCurrent ? "text-primary" : "text-muted-foreground"
                    )}
                  >
                    {step.title}
                  </span>
                </button>

                {/* Connector line */}
                {index < steps.length - 1 && (
                  <div
                    className={cn(
                      "flex-1 h-0.5 mx-2",
                      isStepComplete(step.id)
                        ? "bg-success"
                        : "bg-muted-foreground/20"
                    )}
                  />
                )}
              </li>
            );
          })}
        </ol>
      ) : (
        // Vertical orientation
        <ol className="space-y-2">
          {steps.map((step, index) => {
            const isComplete = isStepComplete(step.id);
            const isCurrent = state.currentStep === step.id;
            const isClickable = index === 0 || isStepComplete(index - 1);

            return (
              <li key={step.id} className="relative">
                {/* Connector line */}
                {index < steps.length - 1 && (
                  <div
                    className={cn(
                      "absolute left-5 top-10 w-0.5 h-8",
                      isStepComplete(step.id)
                        ? "bg-success"
                        : "bg-muted-foreground/20"
                    )}
                  />
                )}

                <button
                  type="button"
                  onClick={() => isClickable && goToStep(step.id)}
                  disabled={!isClickable}
                  className={cn(
                    "flex items-center gap-3 w-full p-2 rounded-lg transition-colors",
                    isCurrent && "bg-primary/5",
                    isClickable && !isCurrent && "hover:bg-muted/50",
                    !isClickable && "cursor-not-allowed opacity-50"
                  )}
                >
                  {/* Step circle */}
                  <span
                    className={cn(
                      "flex items-center justify-center w-8 h-8 rounded-full border-2 text-sm font-medium shrink-0",
                      isComplete && !isCurrent
                        ? "bg-success border-success text-white"
                        : isCurrent
                          ? "bg-primary border-primary text-primary-foreground"
                          : "border-muted-foreground/30 text-muted-foreground"
                    )}
                  >
                    {isComplete && !isCurrent ? (
                      <svg
                        className="w-4 h-4"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    ) : (
                      step.id + 1
                    )}
                  </span>

                  {/* Step info */}
                  <div className="flex-1 text-left">
                    <p
                      className={cn(
                        "text-sm font-medium",
                        isCurrent ? "text-primary" : "text-foreground"
                      )}
                    >
                      {step.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {step.description}
                    </p>
                  </div>

                  {/* Required indicator */}
                  {step.isRequired && !isComplete && (
                    <span className="text-xs text-danger">Required</span>
                  )}
                </button>
              </li>
            );
          })}
        </ol>
      )}
    </nav>
  );
}

export default ProgressIndicator;
