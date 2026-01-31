/**
 * NEURAXIS - Symptom Checker Step
 * Searchable symptom checklist with severity scale and AI suggestions
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useCaseForm } from "@/contexts/CaseFormContext";
import { cn, debounce } from "@/lib/utils";
import type { AISuggestion, SymptomSearchResult } from "@/types/medical-case";
import { useCallback, useEffect, useState } from "react";

const SYMPTOM_CATEGORIES = [
  { id: "general", name: "General" },
  { id: "respiratory", name: "Respiratory" },
  { id: "cardiovascular", name: "Cardiovascular" },
  { id: "gastrointestinal", name: "Gastrointestinal" },
  { id: "neurological", name: "Neurological" },
  { id: "musculoskeletal", name: "Musculoskeletal" },
  { id: "dermatological", name: "Skin" },
  { id: "urinary", name: "Urinary" },
];

export function SymptomCheckerStep() {
  const {
    state,
    addSymptom,
    updateSymptom,
    removeSymptom,
    nextStep,
    prevStep,
  } = useCaseForm();

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SymptomSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [aiSuggestions, setAiSuggestions] = useState<
    AISuggestion["relatedSymptoms"]
  >([]);
  const [isLoadingAI, setIsLoadingAI] = useState(false);

  // Fetch symptom suggestions
  const searchSymptoms = useCallback(
    debounce(async (query: string) => {
      if (query.length < 2) {
        setSearchResults([]);
        return;
      }

      setIsSearching(true);
      try {
        const params = new URLSearchParams({ q: query, limit: "15" });
        if (selectedCategory) params.append("category", selectedCategory);

        const response = await fetch(`/api/symptoms/search?${params}`);
        if (response.ok) {
          const data = await response.json();
          setSearchResults(data.symptoms || []);
        }
      } catch (error) {
        console.error("Symptom search error:", error);
      } finally {
        setIsSearching(false);
      }
    }, 300),
    [selectedCategory]
  );

  useEffect(() => {
    searchSymptoms(searchQuery);
  }, [searchQuery, searchSymptoms]);

  // Get AI-suggested related symptoms
  useEffect(() => {
    const fetchAISuggestions = async () => {
      if (state.symptoms.length === 0 || !state.chiefComplaint) return;

      setIsLoadingAI(true);
      try {
        const response = await fetch("/api/ai/related-symptoms", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chiefComplaint: state.chiefComplaint,
            currentSymptoms: state.symptoms.map((s) => s.name),
            patientAge: state.patient?.age,
            patientGender: state.patient?.gender,
          }),
        });

        if (response.ok) {
          const data = await response.json();
          setAiSuggestions(data.suggestions || []);
        }
      } catch (error) {
        console.error("AI suggestions error:", error);
      } finally {
        setIsLoadingAI(false);
      }
    };

    fetchAISuggestions();
  }, [state.symptoms.length, state.chiefComplaint, state.patient]);

  const handleAddSymptom = (result: SymptomSearchResult) => {
    // Check if already added
    if (state.symptoms.some((s) => s.code === result.code)) return;

    addSymptom({
      code: result.code,
      name: result.name,
      category: result.category,
      severity: result.commonSeverity || 5,
      isAISuggested: false,
    });
    setSearchQuery("");
    setSearchResults([]);
  };

  const handleAddAISuggestion = (
    suggestion: AISuggestion["relatedSymptoms"][0]
  ) => {
    addSymptom({
      code: `AI-${Date.now()}`,
      name: suggestion.symptom,
      category: "ai-suggested",
      severity: 5,
      isAISuggested: true,
    });
  };

  const getSeverityColor = (value: number): string => {
    if (value <= 3) return "bg-success";
    if (value <= 5) return "bg-warning";
    if (value <= 7) return "bg-orange-500";
    return "bg-danger";
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Symptoms</h2>
        <p className="text-sm text-muted-foreground">
          Search and add symptoms with severity levels
        </p>
      </div>

      {/* Search input */}
      <div className="relative">
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <Input
            type="search"
            placeholder="Search symptoms..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
          {isSearching && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
            </div>
          )}
        </div>

        {/* Category filter */}
        <div className="flex gap-1 mt-2 overflow-x-auto pb-2">
          <button
            type="button"
            onClick={() => setSelectedCategory(null)}
            className={cn(
              "px-2 py-1 rounded text-xs whitespace-nowrap transition-colors",
              !selectedCategory
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            )}
          >
            All
          </button>
          {SYMPTOM_CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => setSelectedCategory(cat.id)}
              className={cn(
                "px-2 py-1 rounded text-xs whitespace-nowrap transition-colors",
                selectedCategory === cat.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              )}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Search results */}
        {searchResults.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-card border rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {searchResults.map((symptom) => (
              <button
                key={symptom.id}
                type="button"
                onClick={() => handleAddSymptom(symptom)}
                disabled={state.symptoms.some((s) => s.code === symptom.code)}
                className={cn(
                  "w-full flex items-center justify-between px-3 py-2 text-left hover:bg-muted text-sm",
                  state.symptoms.some((s) => s.code === symptom.code) &&
                    "opacity-50 cursor-not-allowed"
                )}
              >
                <div>
                  <p className="font-medium">{symptom.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {symptom.category} • Code: {symptom.code}
                  </p>
                </div>
                {state.symptoms.some((s) => s.code === symptom.code) ? (
                  <span className="text-xs text-success">Added</span>
                ) : (
                  <svg
                    className="h-4 w-4 text-muted-foreground"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* AI Suggestions */}
      {aiSuggestions.length > 0 && (
        <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
          <div className="flex items-center gap-2 mb-3">
            <svg
              className="h-5 w-5 text-primary"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a2 2 0 0 1 0 4h-1v1a3 3 0 0 1-3 3h-8a3 3 0 0 1-3-3v-1H6a2 2 0 0 1 0-4h1V7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" />
            </svg>
            <h3 className="font-medium text-sm">
              AI-Suggested Related Symptoms
            </h3>
            {isLoadingAI && (
              <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {aiSuggestions.map((suggestion, index) => (
              <button
                key={index}
                type="button"
                onClick={() => handleAddAISuggestion(suggestion)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm bg-primary/10 hover:bg-primary/20 transition-colors"
              >
                <span>{suggestion.symptom}</span>
                <span className="text-xs text-muted-foreground">
                  {Math.round(suggestion.relevance * 100)}%
                </span>
                <svg
                  className="h-3 w-3"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Selected symptoms */}
      <div>
        <h3 className="font-medium text-sm mb-3">
          Selected Symptoms ({state.symptoms.length})
        </h3>

        {state.symptoms.length === 0 ? (
          <div className="text-center py-8 border rounded-lg border-dashed">
            <p className="text-muted-foreground">No symptoms added yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              Search and add symptoms above
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {state.symptoms.map((symptom) => (
              <div key={symptom.id} className="p-4 rounded-lg border bg-card">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium">{symptom.name}</span>
                      {symptom.isAISuggested && (
                        <span className="px-1.5 py-0.5 rounded text-xs bg-primary/10 text-primary">
                          AI Suggested
                        </span>
                      )}
                    </div>

                    {/* Severity slider */}
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-muted-foreground w-16">
                        Severity:
                      </span>
                      <input
                        type="range"
                        min="1"
                        max="10"
                        value={symptom.severity}
                        onChange={(e) =>
                          updateSymptom(symptom.id, {
                            severity: parseInt(e.target.value) as any,
                          })
                        }
                        className="flex-1 h-2 rounded-lg appearance-none cursor-pointer bg-muted"
                      />
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded text-xs font-bold text-white min-w-[3rem] text-center",
                          getSeverityColor(symptom.severity)
                        )}
                      >
                        {symptom.severity}/10
                      </span>
                    </div>

                    {/* Duration */}
                    <div className="flex items-center gap-2 mt-2">
                      <label className="text-xs text-muted-foreground">
                        Duration:
                      </label>
                      <Input
                        placeholder="e.g., 2 days"
                        value={symptom.duration || ""}
                        onChange={(e) =>
                          updateSymptom(symptom.id, {
                            duration: e.target.value,
                          })
                        }
                        className="h-8 text-sm max-w-[150px]"
                      />
                    </div>
                  </div>

                  {/* Remove button */}
                  <button
                    type="button"
                    onClick={() => removeSymptom(symptom.id)}
                    className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-danger"
                  >
                    <svg
                      className="h-5 w-5"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
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
        <Button
          type="button"
          onClick={nextStep}
          disabled={state.symptoms.length === 0}
          size="lg"
        >
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
    </div>
  );
}

export default SymptomCheckerStep;
