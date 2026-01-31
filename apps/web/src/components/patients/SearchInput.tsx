/**
 * NEURAXIS - Patient Search Input
 * Debounced search input with autocomplete
 */

"use client";

import { cn } from "@/lib/utils";
import React, { useCallback, useEffect, useRef, useState } from "react";

interface SearchResult {
  id: string;
  mrn: string;
  name: string;
  dob: string;
}

interface PatientSearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSelect?: (patient: SearchResult) => void;
  placeholder?: string;
  debounceMs?: number;
  showAutocomplete?: boolean;
  className?: string;
}

export function PatientSearchInput({
  value,
  onChange,
  onSelect,
  placeholder = "Search by name, MRN, phone, or email...",
  debounceMs = 300,
  showAutocomplete = true,
  className,
}: PatientSearchInputProps) {
  const [localValue, setLocalValue] = useState(value);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Debounce the onChange callback
  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(localValue);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [localValue, debounceMs, onChange]);

  // Fetch autocomplete results
  useEffect(() => {
    if (!showAutocomplete || localValue.length < 2) {
      setResults([]);
      return;
    }

    const fetchResults = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(
          `/api/patients/autocomplete?q=${encodeURIComponent(localValue)}&limit=8`
        );
        if (response.ok) {
          const data = await response.json();
          setResults(data);
        }
      } catch (error) {
        console.error("Autocomplete error:", error);
      } finally {
        setIsLoading(false);
      }
    };

    const timer = setTimeout(fetchResults, 200);
    return () => clearTimeout(timer);
  }, [localValue, showAutocomplete]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!showResults || results.length === 0) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev < results.length - 1 ? prev + 1 : 0
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev > 0 ? prev - 1 : results.length - 1
          );
          break;
        case "Enter":
          e.preventDefault();
          if (selectedIndex >= 0 && results[selectedIndex]) {
            handleSelect(results[selectedIndex]);
          }
          break;
        case "Escape":
          setShowResults(false);
          setSelectedIndex(-1);
          break;
      }
    },
    [showResults, results, selectedIndex]
  );

  const handleSelect = (patient: SearchResult) => {
    setLocalValue(patient.name);
    onChange(patient.name);
    setShowResults(false);
    setSelectedIndex(-1);
    onSelect?.(patient);
  };

  // Close results when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        resultsRef.current &&
        !resultsRef.current.contains(e.target as Node) &&
        !inputRef.current?.contains(e.target as Node)
      ) {
        setShowResults(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className={cn("relative", className)}>
      <div className="relative">
        {/* Search icon */}
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" />
        </svg>

        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          value={localValue}
          onChange={(e) => {
            setLocalValue(e.target.value);
            setShowResults(true);
            setSelectedIndex(-1);
          }}
          onFocus={() => setShowResults(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={cn(
            "flex h-10 w-full rounded-md border border-input bg-background",
            "pl-10 pr-10 py-2 text-sm",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
            "placeholder:text-muted-foreground"
          )}
          aria-label="Search patients"
          aria-expanded={showResults && results.length > 0}
          aria-controls="search-results"
          aria-autocomplete="list"
        />

        {/* Loading spinner */}
        {isLoading && (
          <svg
            className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        )}

        {/* Clear button */}
        {localValue && !isLoading && (
          <button
            type="button"
            onClick={() => {
              setLocalValue("");
              onChange("");
              setResults([]);
              inputRef.current?.focus();
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label="Clear search"
          >
            <svg
              className="h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Autocomplete results */}
      {showResults && showAutocomplete && results.length > 0 && (
        <div
          ref={resultsRef}
          id="search-results"
          role="listbox"
          className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-lg max-h-80 overflow-auto"
        >
          {results.map((patient, index) => (
            <div
              key={patient.id}
              role="option"
              aria-selected={index === selectedIndex}
              onClick={() => handleSelect(patient)}
              className={cn(
                "flex items-center justify-between px-3 py-2 cursor-pointer",
                "hover:bg-muted",
                index === selectedIndex && "bg-muted"
              )}
            >
              <div>
                <p className="text-sm font-medium">{patient.name}</p>
                <p className="text-xs text-muted-foreground">
                  MRN: {patient.mrn} • DOB: {patient.dob}
                </p>
              </div>
              <svg
                className="h-4 w-4 text-muted-foreground"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="m9 18 6-6-6-6" />
              </svg>
            </div>
          ))}
        </div>
      )}

      {/* No results message */}
      {showResults &&
        showAutocomplete &&
        localValue.length >= 2 &&
        results.length === 0 &&
        !isLoading && (
          <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover p-4 text-center text-sm text-muted-foreground">
            No patients found
          </div>
        )}
    </div>
  );
}

export default PatientSearchInput;
