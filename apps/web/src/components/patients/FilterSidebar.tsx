/**
 * NEURAXIS - Patient Filter Sidebar
 * Advanced filtering options for patient list
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/utils";
import type {
  Gender,
  PatientSearchFilters,
  PatientStatus,
} from "@/types/patient-search";
import React, { useState } from "react";

interface FilterSidebarProps {
  filters: PatientSearchFilters;
  onFiltersChange: (filters: PatientSearchFilters) => void;
  onReset: () => void;
  facets?: {
    status: Record<string, number>;
    gender: Record<string, number>;
    ageRanges: Record<string, number>;
    topConditions: Array<{ condition: string; count: number }>;
  };
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  className?: string;
}

const STATUS_OPTIONS: { value: PatientStatus; label: string; color: string }[] =
  [
    { value: "active", label: "Active", color: "bg-success" },
    { value: "inactive", label: "Inactive", color: "bg-muted-foreground" },
    { value: "deceased", label: "Deceased", color: "bg-danger" },
    { value: "transferred", label: "Transferred", color: "bg-warning" },
  ];

const GENDER_OPTIONS: { value: Gender; label: string }[] = [
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "other", label: "Other" },
  { value: "prefer_not_to_say", label: "Prefer not to say" },
];

const AGE_RANGE_OPTIONS = [
  { label: "Pediatric (0-17)", min: 0, max: 17 },
  { label: "Young Adult (18-30)", min: 18, max: 30 },
  { label: "Adult (31-50)", min: 31, max: 50 },
  { label: "Senior (51-70)", min: 51, max: 70 },
  { label: "Elderly (71+)", min: 71, max: null },
];

export function FilterSidebar({
  filters,
  onFiltersChange,
  onReset,
  facets,
  isCollapsed = false,
  onToggleCollapse,
  className,
}: FilterSidebarProps) {
  const [expandedSections, setExpandedSections] = useState<
    Record<string, boolean>
  >({
    status: true,
    gender: true,
    age: true,
    conditions: false,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const toggleStatus = (status: PatientStatus) => {
    const current = filters.status || [];
    const updated = current.includes(status)
      ? current.filter((s) => s !== status)
      : [...current, status];
    onFiltersChange({ ...filters, status: updated });
  };

  const toggleGender = (gender: Gender) => {
    const current = filters.gender || [];
    const updated = current.includes(gender)
      ? current.filter((g) => g !== gender)
      : [...current, gender];
    onFiltersChange({ ...filters, gender: updated });
  };

  const setAgeRange = (min: number | null, max: number | null) => {
    onFiltersChange({
      ...filters,
      ageRange: [min, max],
    });
  };

  const toggleCondition = (condition: string) => {
    const current = filters.conditions || [];
    const updated = current.includes(condition)
      ? current.filter((c) => c !== condition)
      : [...current, condition];
    onFiltersChange({ ...filters, conditions: updated });
  };

  const toggleAllergies = () => {
    onFiltersChange({
      ...filters,
      hasAllergies: filters.hasAllergies === true ? null : true,
    });
  };

  const activeFilterCount =
    (filters.status?.length || 0) +
    (filters.gender?.length || 0) +
    (filters.ageRange?.[0] != null || filters.ageRange?.[1] != null ? 1 : 0) +
    (filters.conditions?.length || 0) +
    (filters.hasAllergies ? 1 : 0);

  if (isCollapsed) {
    return (
      <div
        className={cn(
          "w-12 border-r bg-card flex flex-col items-center py-4",
          className
        )}
      >
        <button
          onClick={onToggleCollapse}
          className="p-2 rounded-md hover:bg-muted"
          aria-label="Expand filters"
        >
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M3 6h18M3 12h18M3 18h18" />
          </svg>
          {activeFilterCount > 0 && (
            <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </button>
      </div>
    );
  }

  return (
    <aside className={cn("w-64 border-r bg-card flex flex-col", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <h2 className="font-semibold text-sm flex items-center gap-2">
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
          </svg>
          Filters
          {activeFilterCount > 0 && (
            <span className="h-5 w-5 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </h2>
        <div className="flex items-center gap-1">
          {activeFilterCount > 0 && (
            <Button variant="ghost" size="xs" onClick={onReset}>
              Clear
            </Button>
          )}
          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="p-1 rounded hover:bg-muted"
              aria-label="Collapse filters"
            >
              <svg
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="m15 18-6-6 6-6" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Filter sections */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Status filter */}
        <FilterSection
          title="Status"
          isExpanded={expandedSections.status}
          onToggle={() => toggleSection("status")}
        >
          <div className="space-y-2">
            {STATUS_OPTIONS.map((option) => (
              <label
                key={option.value}
                className="flex items-center gap-2 cursor-pointer group"
              >
                <input
                  type="checkbox"
                  checked={filters.status?.includes(option.value) || false}
                  onChange={() => toggleStatus(option.value)}
                  className="rounded border-input text-primary focus:ring-primary"
                />
                <span className={cn("h-2 w-2 rounded-full", option.color)} />
                <span className="text-sm flex-1 group-hover:text-foreground">
                  {option.label}
                </span>
                {facets?.status[option.value] != null && (
                  <span className="text-xs text-muted-foreground">
                    {facets.status[option.value]}
                  </span>
                )}
              </label>
            ))}
          </div>
        </FilterSection>

        {/* Gender filter */}
        <FilterSection
          title="Gender"
          isExpanded={expandedSections.gender}
          onToggle={() => toggleSection("gender")}
        >
          <div className="space-y-2">
            {GENDER_OPTIONS.map((option) => (
              <label
                key={option.value}
                className="flex items-center gap-2 cursor-pointer group"
              >
                <input
                  type="checkbox"
                  checked={filters.gender?.includes(option.value) || false}
                  onChange={() => toggleGender(option.value)}
                  className="rounded border-input text-primary focus:ring-primary"
                />
                <span className="text-sm flex-1 group-hover:text-foreground">
                  {option.label}
                </span>
                {facets?.gender[option.value] != null && (
                  <span className="text-xs text-muted-foreground">
                    {facets.gender[option.value]}
                  </span>
                )}
              </label>
            ))}
          </div>
        </FilterSection>

        {/* Age range filter */}
        <FilterSection
          title="Age Range"
          isExpanded={expandedSections.age}
          onToggle={() => toggleSection("age")}
        >
          <div className="space-y-3">
            {/* Quick presets */}
            <div className="flex flex-wrap gap-1">
              {AGE_RANGE_OPTIONS.map((option) => {
                const isSelected =
                  filters.ageRange?.[0] === option.min &&
                  filters.ageRange?.[1] === option.max;
                return (
                  <button
                    key={option.label}
                    onClick={() => setAgeRange(option.min, option.max)}
                    className={cn(
                      "px-2 py-1 text-xs rounded-full border transition-colors",
                      isSelected
                        ? "bg-primary text-primary-foreground border-primary"
                        : "hover:bg-muted border-input"
                    )}
                  >
                    {option.label.split(" ")[0]}
                  </button>
                );
              })}
            </div>

            {/* Custom range */}
            <div className="flex items-center gap-2">
              <Input
                type="number"
                placeholder="Min"
                value={filters.ageRange?.[0] ?? ""}
                onChange={(e) =>
                  setAgeRange(
                    e.target.value ? parseInt(e.target.value, 10) : null,
                    filters.ageRange?.[1] ?? null
                  )
                }
                className="h-8 text-sm"
                min={0}
                max={150}
              />
              <span className="text-muted-foreground">to</span>
              <Input
                type="number"
                placeholder="Max"
                value={filters.ageRange?.[1] ?? ""}
                onChange={(e) =>
                  setAgeRange(
                    filters.ageRange?.[0] ?? null,
                    e.target.value ? parseInt(e.target.value, 10) : null
                  )
                }
                className="h-8 text-sm"
                min={0}
                max={150}
              />
            </div>
          </div>
        </FilterSection>

        {/* Conditions filter */}
        {facets?.topConditions && facets.topConditions.length > 0 && (
          <FilterSection
            title="Conditions"
            isExpanded={expandedSections.conditions}
            onToggle={() => toggleSection("conditions")}
          >
            <div className="space-y-2">
              {facets.topConditions.slice(0, 8).map((item) => (
                <label
                  key={item.condition}
                  className="flex items-center gap-2 cursor-pointer group"
                >
                  <input
                    type="checkbox"
                    checked={
                      filters.conditions?.includes(item.condition) || false
                    }
                    onChange={() => toggleCondition(item.condition)}
                    className="rounded border-input text-primary focus:ring-primary"
                  />
                  <span className="text-sm flex-1 truncate group-hover:text-foreground">
                    {item.condition}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {item.count}
                  </span>
                </label>
              ))}
            </div>
          </FilterSection>
        )}

        {/* Allergies filter */}
        <div className="pt-2 border-t">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.hasAllergies === true}
              onChange={toggleAllergies}
              className="rounded border-input text-primary focus:ring-primary"
            />
            <span className="text-sm">Has documented allergies</span>
          </label>
        </div>
      </div>
    </aside>
  );
}

// Filter section component
function FilterSection({
  title,
  isExpanded,
  onToggle,
  children,
}: {
  title: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="border-b pb-4">
      <button
        type="button"
        onClick={onToggle}
        className="flex items-center justify-between w-full text-sm font-medium mb-2"
      >
        {title}
        <svg
          className={cn(
            "h-4 w-4 transition-transform",
            isExpanded && "rotate-180"
          )}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>
      {isExpanded && children}
    </div>
  );
}

export default FilterSidebar;
