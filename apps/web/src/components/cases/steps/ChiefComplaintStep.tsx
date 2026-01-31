/**
 * NEURAXIS - Chief Complaint Step
 * Free text complaint entry with suggestions
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { useCaseForm } from "@/contexts/CaseFormContext";
import { cn, debounce } from "@/lib/utils";
import {
  chiefComplaintSchema,
  type ChiefComplaintInput,
} from "@/lib/validations/case";
import { zodResolver } from "@hookform/resolvers/zod";
import { useCallback, useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";

const COMMON_COMPLAINTS = [
  "Chest pain",
  "Shortness of breath",
  "Abdominal pain",
  "Headache",
  "Back pain",
  "Fever",
  "Cough",
  "Nausea/Vomiting",
  "Dizziness",
  "Fatigue",
  "Joint pain",
  "Skin rash",
];

const AGGRAVATING_FACTORS = [
  "Movement",
  "Eating",
  "Breathing deeply",
  "Lying down",
  "Standing",
  "Walking",
  "Stress",
  "Physical activity",
  "Cold weather",
];

const RELIEVING_FACTORS = [
  "Rest",
  "Medication",
  "Heat",
  "Cold",
  "Position change",
  "Eating",
  "Deep breathing",
  "Sleep",
];

export function ChiefComplaintStep() {
  const { state, setChiefComplaint, nextStep, prevStep } = useCaseForm();
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ChiefComplaintInput>({
    resolver: zodResolver(chiefComplaintSchema),
    defaultValues: state.chiefComplaint || {
      complaint: "",
      duration: "",
      durationUnit: "days",
      onset: "gradual",
      severity: 5,
      location: "",
      character: "",
      aggravatingFactors: [],
      relievingFactors: [],
    },
  });

  const complaint = watch("complaint");
  const severity = watch("severity");

  // Fetch complaint suggestions
  const fetchSuggestions = useCallback(
    debounce(async (query: string) => {
      if (query.length < 2) {
        setSuggestions([]);
        return;
      }
      try {
        const response = await fetch(
          `/api/symptoms/autocomplete?q=${encodeURIComponent(query)}&type=complaint`
        );
        if (response.ok) {
          const data = await response.json();
          setSuggestions(data.suggestions || []);
        }
      } catch (error) {
        // Fall back to local suggestions
        const filtered = COMMON_COMPLAINTS.filter((c) =>
          c.toLowerCase().includes(query.toLowerCase())
        );
        setSuggestions(filtered);
      }
    }, 300),
    []
  );

  useEffect(() => {
    fetchSuggestions(complaint);
  }, [complaint, fetchSuggestions]);

  const onSubmit = (data: ChiefComplaintInput) => {
    setChiefComplaint(data);
    nextStep();
  };

  const getSeverityLabel = (value: number): string => {
    if (value <= 2) return "Mild";
    if (value <= 4) return "Moderate";
    if (value <= 6) return "Moderate-Severe";
    if (value <= 8) return "Severe";
    return "Very Severe";
  };

  const getSeverityColor = (value: number): string => {
    if (value <= 2) return "text-success";
    if (value <= 4) return "text-info";
    if (value <= 6) return "text-warning";
    if (value <= 8) return "text-orange-500";
    return "text-danger";
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Chief Complaint</h2>
        <p className="text-sm text-muted-foreground">
          What is the primary reason for this visit?
        </p>
      </div>

      {/* Main complaint */}
      <div className="relative">
        <label className="text-sm font-medium mb-1.5 block">
          Primary Complaint *
        </label>
        <Textarea
          {...register("complaint")}
          placeholder="Describe the patient's main complaint..."
          rows={3}
          className="text-base"
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
        />
        {errors.complaint && (
          <p className="text-xs text-danger mt-1">{errors.complaint.message}</p>
        )}

        {/* Suggestions dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-card border rounded-lg shadow-lg max-h-48 overflow-y-auto">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                type="button"
                onClick={() => {
                  setValue("complaint", suggestion);
                  setShowSuggestions(false);
                }}
                className="w-full px-3 py-2 text-left hover:bg-muted text-sm"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {/* Quick select chips */}
        <div className="flex flex-wrap gap-2 mt-2">
          {COMMON_COMPLAINTS.slice(0, 6).map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setValue("complaint", c)}
              className={cn(
                "px-2 py-1 rounded-full text-xs border transition-colors",
                complaint === c
                  ? "bg-primary text-primary-foreground border-primary"
                  : "hover:bg-muted border-input"
              )}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Duration and Onset */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className="text-sm font-medium mb-1.5 block">Duration *</label>
          <Input
            type="number"
            {...register("duration")}
            placeholder="e.g., 3"
            min="0"
          />
          {errors.duration && (
            <p className="text-xs text-danger mt-1">
              {errors.duration.message}
            </p>
          )}
        </div>
        <div>
          <label className="text-sm font-medium mb-1.5 block">Unit</label>
          <select
            {...register("durationUnit")}
            className="w-full h-10 px-3 rounded-md border bg-background"
          >
            <option value="hours">Hours</option>
            <option value="days">Days</option>
            <option value="weeks">Weeks</option>
            <option value="months">Months</option>
          </select>
        </div>
        <div className="col-span-2">
          <label className="text-sm font-medium mb-1.5 block">Onset *</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                value="sudden"
                {...register("onset")}
                className="w-4 h-4 text-primary"
              />
              <span className="text-sm">Sudden</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                value="gradual"
                {...register("onset")}
                className="w-4 h-4 text-primary"
              />
              <span className="text-sm">Gradual</span>
            </label>
          </div>
        </div>
      </div>

      {/* Severity slider */}
      <div>
        <label className="text-sm font-medium mb-1.5 block">
          Severity *
          <span className={cn("ml-2 font-bold", getSeverityColor(severity))}>
            {severity}/10 - {getSeverityLabel(severity)}
          </span>
        </label>
        <div className="relative mt-2">
          <Controller
            name="severity"
            control={control}
            render={({ field }) => (
              <input
                type="range"
                min="1"
                max="10"
                {...field}
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
            )}
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>1 - Mild</span>
            <span>10 - Severe</span>
          </div>
        </div>
      </div>

      {/* Location and Character */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium mb-1.5 block">Location</label>
          <Input
            {...register("location")}
            placeholder="e.g., Lower right abdomen"
          />
        </div>
        <div>
          <label className="text-sm font-medium mb-1.5 block">Character</label>
          <Input
            {...register("character")}
            placeholder="e.g., Sharp, dull, burning"
          />
        </div>
      </div>

      {/* Aggravating Factors */}
      <div>
        <label className="text-sm font-medium mb-1.5 block">
          Aggravating Factors
        </label>
        <Controller
          name="aggravatingFactors"
          control={control}
          render={({ field }) => (
            <div className="flex flex-wrap gap-2">
              {AGGRAVATING_FACTORS.map((factor) => (
                <button
                  key={factor}
                  type="button"
                  onClick={() => {
                    const current = field.value || [];
                    const updated = current.includes(factor)
                      ? current.filter((f) => f !== factor)
                      : [...current, factor];
                    field.onChange(updated);
                  }}
                  className={cn(
                    "px-3 py-1.5 rounded-full text-xs border transition-colors",
                    (field.value || []).includes(factor)
                      ? "bg-danger/10 text-danger border-danger/30"
                      : "hover:bg-muted border-input"
                  )}
                >
                  {factor}
                </button>
              ))}
            </div>
          )}
        />
      </div>

      {/* Relieving Factors */}
      <div>
        <label className="text-sm font-medium mb-1.5 block">
          Relieving Factors
        </label>
        <Controller
          name="relievingFactors"
          control={control}
          render={({ field }) => (
            <div className="flex flex-wrap gap-2">
              {RELIEVING_FACTORS.map((factor) => (
                <button
                  key={factor}
                  type="button"
                  onClick={() => {
                    const current = field.value || [];
                    const updated = current.includes(factor)
                      ? current.filter((f) => f !== factor)
                      : [...current, factor];
                    field.onChange(updated);
                  }}
                  className={cn(
                    "px-3 py-1.5 rounded-full text-xs border transition-colors",
                    (field.value || []).includes(factor)
                      ? "bg-success/10 text-success border-success/30"
                      : "hover:bg-muted border-input"
                  )}
                >
                  {factor}
                </button>
              ))}
            </div>
          )}
        />
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

export default ChiefComplaintStep;
