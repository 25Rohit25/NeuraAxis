/**
 * NEURAXIS - Vital Signs Step
 * Entry form for vital measurements with normal range indicators
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useCaseForm } from "@/contexts/CaseFormContext";
import { cn } from "@/lib/utils";
import { vitalSignsSchema, type VitalSignsInput } from "@/lib/validations/case";
import { VITAL_NORMAL_RANGES } from "@/types/medical-case";
import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";

export function VitalSignsStep() {
  const { state, setVitals, nextStep, prevStep } = useCaseForm();

  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<VitalSignsInput>({
    resolver: zodResolver(vitalSignsSchema),
    defaultValues: state.vitals || {
      bloodPressureSystolic: 120,
      bloodPressureDiastolic: 80,
      heartRate: 72,
      temperature: 98.6,
      temperatureUnit: "F",
      oxygenSaturation: 98,
      respiratoryRate: 16,
      recordedAt: new Date().toISOString(),
    },
  });

  const watchedValues = watch();

  const onSubmit = (data: VitalSignsInput) => {
    setVitals(data);
    nextStep();
  };

  const isAbnormal = (
    field: string,
    value: number
  ): "low" | "high" | "normal" => {
    const range = VITAL_NORMAL_RANGES[field];
    if (!range) return "normal";
    if (value < range.min) return "low";
    if (value > range.max) return "high";
    return "normal";
  };

  const getVitalStatusColor = (status: "low" | "high" | "normal"): string => {
    if (status === "low") return "border-info bg-info/5";
    if (status === "high") return "border-danger bg-danger/5";
    return "border-success bg-success/5";
  };

  const getVitalStatusIcon = (status: "low" | "high" | "normal") => {
    if (status === "low")
      return (
        <svg
          className="h-4 w-4 text-info"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
          <polyline points="17 18 23 18 23 12" />
        </svg>
      );
    if (status === "high")
      return (
        <svg
          className="h-4 w-4 text-danger"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
          <polyline points="17 6 23 6 23 12" />
        </svg>
      );
    return (
      <svg
        className="h-4 w-4 text-success"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <polyline points="20 6 9 17 4 12" />
      </svg>
    );
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Vital Signs</h2>
        <p className="text-sm text-muted-foreground">
          Enter current vital measurements
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Blood Pressure */}
        <div
          className={cn(
            "p-4 rounded-lg border-2 transition-colors",
            getVitalStatusColor(
              isAbnormal(
                "bloodPressureSystolic",
                watchedValues.bloodPressureSystolic
              ) === "normal" &&
                isAbnormal(
                  "bloodPressureDiastolic",
                  watchedValues.bloodPressureDiastolic
                ) === "normal"
                ? "normal"
                : "high"
            )
          )}
        >
          <div className="flex items-center justify-between mb-3">
            <label className="font-medium flex items-center gap-2">
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
              Blood Pressure
            </label>
            {getVitalStatusIcon(
              isAbnormal(
                "bloodPressureSystolic",
                watchedValues.bloodPressureSystolic
              ) === "normal" &&
                isAbnormal(
                  "bloodPressureDiastolic",
                  watchedValues.bloodPressureDiastolic
                ) === "normal"
                ? "normal"
                : "high"
            )}
          </div>
          <div className="flex items-center gap-2">
            <div className="flex-1">
              <Input
                type="number"
                {...register("bloodPressureSystolic", { valueAsNumber: true })}
                className="text-center text-lg font-bold"
              />
              <p className="text-xs text-muted-foreground text-center mt-1">
                Systolic
              </p>
            </div>
            <span className="text-2xl text-muted-foreground">/</span>
            <div className="flex-1">
              <Input
                type="number"
                {...register("bloodPressureDiastolic", { valueAsNumber: true })}
                className="text-center text-lg font-bold"
              />
              <p className="text-xs text-muted-foreground text-center mt-1">
                Diastolic
              </p>
            </div>
            <span className="text-sm text-muted-foreground">mmHg</span>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Normal: 90-120 / 60-80 mmHg
          </p>
          {(errors.bloodPressureSystolic || errors.bloodPressureDiastolic) && (
            <p className="text-xs text-danger mt-1">
              {errors.bloodPressureSystolic?.message ||
                errors.bloodPressureDiastolic?.message}
            </p>
          )}
        </div>

        {/* Heart Rate */}
        <div
          className={cn(
            "p-4 rounded-lg border-2 transition-colors",
            getVitalStatusColor(
              isAbnormal("heartRate", watchedValues.heartRate)
            )
          )}
        >
          <div className="flex items-center justify-between mb-3">
            <label className="font-medium flex items-center gap-2">
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
              </svg>
              Heart Rate
            </label>
            {getVitalStatusIcon(
              isAbnormal("heartRate", watchedValues.heartRate)
            )}
          </div>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              {...register("heartRate", { valueAsNumber: true })}
              className="text-center text-2xl font-bold"
            />
            <span className="text-sm text-muted-foreground">bpm</span>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Normal: 60-100 bpm
          </p>
          {errors.heartRate && (
            <p className="text-xs text-danger mt-1">
              {errors.heartRate.message}
            </p>
          )}
        </div>

        {/* Temperature */}
        <div
          className={cn(
            "p-4 rounded-lg border-2 transition-colors",
            getVitalStatusColor(
              isAbnormal(
                watchedValues.temperatureUnit === "F"
                  ? "temperatureF"
                  : "temperatureC",
                watchedValues.temperature
              )
            )
          )}
        >
          <div className="flex items-center justify-between mb-3">
            <label className="font-medium flex items-center gap-2">
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z" />
              </svg>
              Temperature
            </label>
            {getVitalStatusIcon(
              isAbnormal(
                watchedValues.temperatureUnit === "F"
                  ? "temperatureF"
                  : "temperatureC",
                watchedValues.temperature
              )
            )}
          </div>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              step="0.1"
              {...register("temperature", { valueAsNumber: true })}
              className="text-center text-2xl font-bold"
            />
            <select
              {...register("temperatureUnit")}
              className="h-10 px-2 rounded-md border bg-background"
            >
              <option value="F">°F</option>
              <option value="C">°C</option>
            </select>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Normal: 97.8-99.1°F / 36.5-37.3°C
          </p>
          {errors.temperature && (
            <p className="text-xs text-danger mt-1">
              {errors.temperature.message}
            </p>
          )}
        </div>

        {/* Oxygen Saturation */}
        <div
          className={cn(
            "p-4 rounded-lg border-2 transition-colors",
            getVitalStatusColor(
              isAbnormal("oxygenSaturation", watchedValues.oxygenSaturation)
            )
          )}
        >
          <div className="flex items-center justify-between mb-3">
            <label className="font-medium flex items-center gap-2">
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle cx="12" cy="12" r="10" />
                <path d="M12 2a10 10 0 0 1 0 20" />
              </svg>
              O₂ Saturation
            </label>
            {getVitalStatusIcon(
              isAbnormal("oxygenSaturation", watchedValues.oxygenSaturation)
            )}
          </div>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              {...register("oxygenSaturation", { valueAsNumber: true })}
              className="text-center text-2xl font-bold"
            />
            <span className="text-sm text-muted-foreground">%</span>
          </div>
          <p className="text-xs text-muted-foreground mt-2">Normal: 95-100%</p>
          {errors.oxygenSaturation && (
            <p className="text-xs text-danger mt-1">
              {errors.oxygenSaturation.message}
            </p>
          )}
        </div>

        {/* Respiratory Rate */}
        <div
          className={cn(
            "p-4 rounded-lg border-2 transition-colors",
            getVitalStatusColor(
              isAbnormal("respiratoryRate", watchedValues.respiratoryRate)
            )
          )}
        >
          <div className="flex items-center justify-between mb-3">
            <label className="font-medium flex items-center gap-2">
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z" />
                <path d="M12 6v6l4 2" />
              </svg>
              Respiratory Rate
            </label>
            {getVitalStatusIcon(
              isAbnormal("respiratoryRate", watchedValues.respiratoryRate)
            )}
          </div>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              {...register("respiratoryRate", { valueAsNumber: true })}
              className="text-center text-2xl font-bold"
            />
            <span className="text-sm text-muted-foreground">/min</span>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Normal: 12-20 /min
          </p>
          {errors.respiratoryRate && (
            <p className="text-xs text-danger mt-1">
              {errors.respiratoryRate.message}
            </p>
          )}
        </div>

        {/* Pain Level */}
        <div className="p-4 rounded-lg border-2 border-muted">
          <label className="font-medium flex items-center gap-2 mb-3">
            <svg
              className="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M8 15h8" />
              <circle cx="9" cy="9" r="1" />
              <circle cx="15" cy="9" r="1" />
            </svg>
            Pain Level
          </label>
          <Controller
            name="painLevel"
            control={control}
            render={({ field }) => (
              <div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={field.value || 1}
                  onChange={(e) => field.onChange(parseInt(e.target.value))}
                  className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                  style={{
                    background: `linear-gradient(to right, 
                      #22c55e 0%, 
                      #eab308 40%, 
                      #f97316 60%, 
                      #ef4444 100%)`,
                  }}
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>None</span>
                  <span className="font-bold">{field.value || 1}/10</span>
                  <span>Severe</span>
                </div>
              </div>
            )}
          />
        </div>
      </div>

      {/* Weight & Height (optional) */}
      <div className="p-4 rounded-lg border bg-muted/30">
        <h4 className="font-medium mb-3">Optional Measurements</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="text-sm text-muted-foreground mb-1 block">
              Weight
            </label>
            <div className="flex gap-1">
              <Input
                type="number"
                step="0.1"
                {...register("weight", { valueAsNumber: true })}
                placeholder="—"
              />
              <select
                {...register("weightUnit")}
                className="h-10 px-1 rounded-md border bg-background text-sm"
              >
                <option value="lbs">lbs</option>
                <option value="kg">kg</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-sm text-muted-foreground mb-1 block">
              Height
            </label>
            <div className="flex gap-1">
              <Input
                type="number"
                step="0.1"
                {...register("height", { valueAsNumber: true })}
                placeholder="—"
              />
              <select
                {...register("heightUnit")}
                className="h-10 px-1 rounded-md border bg-background text-sm"
              >
                <option value="in">in</option>
                <option value="cm">cm</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t">
        <Button type="button" variant="outline" onClick={prevStep}>
          <svg
            className="h-4 w-4 mr-2"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Back
        </Button>
        <Button type="submit" size="lg">
          Continue
          <svg
            className="h-4 w-4 ml-2"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </Button>
      </div>
    </form>
  );
}

export default VitalSignsStep;
