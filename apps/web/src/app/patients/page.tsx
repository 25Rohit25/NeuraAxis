/**
 * NEURAXIS - Patient List Page
 * Advanced patient search and listing with filters
 */

"use client";

import { DashboardLayout, PageHeader } from "@/components/layout/Layout";
import { BulkActionsBar } from "@/components/patients/BulkActionsBar";
import { FilterSidebar } from "@/components/patients/FilterSidebar";
import { PatientTable } from "@/components/patients/PatientTable";
import { PatientSearchInput } from "@/components/patients/SearchInput";
import { Button } from "@/components/ui/Button";
import { Pagination } from "@/components/ui/Navigation";
import { useToast } from "@/components/ui/Toast";
import type {
  PatientListItem,
  PatientSearchFilters,
  QuickFilter,
  SortDirection,
  SortField,
} from "@/types/patient-search";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState, useTransition } from "react";

// Quick filter presets
const QUICK_FILTERS: QuickFilter[] = [
  { id: "all", label: "All", params: {} },
  { id: "active", label: "Active", params: { status: "active" } },
  { id: "recent", label: "Recent", params: {} },
  { id: "elderly", label: "65+", params: { ageMin: 65 } },
  { id: "pediatric", label: "0-17", params: { ageMax: 17 } },
];

// Default filter state
const defaultFilters: PatientSearchFilters = {
  status: [],
  gender: [],
  ageRange: [null, null],
  conditions: [],
  hasAllergies: null,
  dateRange: {
    createdAfter: null,
    createdBefore: null,
  },
};

export default function PatientsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { success, error } = useToast();
  const [isPending, startTransition] = useTransition();

  // State
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "");
  const [filters, setFilters] = useState<PatientSearchFilters>(defaultFilters);
  const [sortBy, setSortBy] = useState<SortField>("createdAt");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isFilterCollapsed, setIsFilterCollapsed] = useState(false);
  const [activeQuickFilter, setActiveQuickFilter] = useState("all");

  // Data state (in production, this would come from React Query)
  const [patients, setPatients] = useState<PatientListItem[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [facets, setFacets] = useState<any>(null);

  // Fetch patients
  const fetchPatients = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();

      if (searchQuery) params.set("q", searchQuery);
      if (filters.status.length)
        filters.status.forEach((s) => params.append("status", s));
      if (filters.gender.length)
        filters.gender.forEach((g) => params.append("gender", g));
      if (filters.ageRange[0] != null)
        params.set("age_min", filters.ageRange[0].toString());
      if (filters.ageRange[1] != null)
        params.set("age_max", filters.ageRange[1].toString());
      if (filters.hasAllergies != null)
        params.set("has_allergies", filters.hasAllergies.toString());

      params.set("sort_by", sortBy);
      params.set("sort_direction", sortDirection);
      params.set("page", currentPage.toString());
      params.set("page_size", "20");
      params.set("include_facets", "true");

      const response = await fetch(`/api/patients/search?${params.toString()}`);

      if (response.ok) {
        const data = await response.json();
        setPatients(data.items);
        setTotalPages(data.total_pages);
        setTotalCount(data.total);
        setFacets(data.facets);
      }
    } catch (err) {
      console.error("Failed to fetch patients:", err);
      error("Error", "Failed to load patients");
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, filters, sortBy, sortDirection, currentPage, error]);

  // Initial fetch and refetch on filter changes
  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  // Update URL with search params
  useEffect(() => {
    const params = new URLSearchParams();
    if (searchQuery) params.set("q", searchQuery);
    if (currentPage > 1) params.set("page", currentPage.toString());
    if (sortBy !== "createdAt") params.set("sortBy", sortBy);
    if (sortDirection !== "desc") params.set("sortDirection", sortDirection);

    const url = params.toString() ? `?${params.toString()}` : "/patients";
    router.replace(url, { scroll: false });
  }, [searchQuery, currentPage, sortBy, sortDirection, router]);

  // Handlers
  const handleSearch = useCallback((value: string) => {
    setSearchQuery(value);
    setCurrentPage(1);
    setSelectedIds([]);
  }, []);

  const handleSort = useCallback(
    (field: SortField, direction: SortDirection) => {
      setSortBy(field);
      setSortDirection(direction);
      setCurrentPage(1);
    },
    []
  );

  const handleFiltersChange = useCallback(
    (newFilters: PatientSearchFilters) => {
      setFilters(newFilters);
      setCurrentPage(1);
      setSelectedIds([]);
      setActiveQuickFilter("");
    },
    []
  );

  const handleResetFilters = useCallback(() => {
    setFilters(defaultFilters);
    setSearchQuery("");
    setCurrentPage(1);
    setSelectedIds([]);
    setActiveQuickFilter("all");
  }, []);

  const handleQuickFilter = useCallback((filter: QuickFilter) => {
    setActiveQuickFilter(filter.id);
    setFilters({
      ...defaultFilters,
      status: filter.params.status ? [filter.params.status as any] : [],
      ageRange: [filter.params.ageMin ?? null, filter.params.ageMax ?? null],
    });
    setCurrentPage(1);
    setSelectedIds([]);
  }, []);

  const handleRowClick = useCallback(
    (patient: PatientListItem) => {
      router.push(`/patients/${patient.id}`);
    },
    [router]
  );

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
    setSelectedIds([]);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  // Bulk actions
  const handleBulkExport = async () => {
    startTransition(async () => {
      try {
        // In production, call export API
        success(
          "Export Started",
          `Exporting ${selectedIds.length} patients...`
        );
        setSelectedIds([]);
      } catch (err) {
        error("Export Failed", "Failed to export patients");
      }
    });
  };

  const handleBulkArchive = async () => {
    startTransition(async () => {
      try {
        await fetch("/api/patients/bulk-action", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "archive", patient_ids: selectedIds }),
        });
        success("Archived", `${selectedIds.length} patients archived`);
        setSelectedIds([]);
        fetchPatients();
      } catch (err) {
        error("Archive Failed", "Failed to archive patients");
      }
    });
  };

  const handleBulkActivate = async () => {
    startTransition(async () => {
      try {
        await fetch("/api/patients/bulk-action", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "activate",
            patient_ids: selectedIds,
          }),
        });
        success("Activated", `${selectedIds.length} patients activated`);
        setSelectedIds([]);
        fetchPatients();
      } catch (err) {
        error("Activation Failed", "Failed to activate patients");
      }
    });
  };

  const handleBulkDelete = async () => {
    startTransition(async () => {
      try {
        await fetch("/api/patients/bulk-action", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "delete", patient_ids: selectedIds }),
        });
        success("Deleted", `${selectedIds.length} patients deleted`);
        setSelectedIds([]);
        fetchPatients();
      } catch (err) {
        error("Delete Failed", "Failed to delete patients");
      }
    });
  };

  return (
    <DashboardLayout>
      <PageHeader
        title="Patients"
        description={`${totalCount.toLocaleString()} total patients`}
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Patients" },
        ]}
        actions={
          <Link href="/patients/new">
            <Button
              leftIcon={
                <svg
                  className="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M12 5v14M5 12h14" />
                </svg>
              }
            >
              New Patient
            </Button>
          </Link>
        }
      />

      <div className="flex gap-6 mt-6">
        {/* Filter sidebar */}
        <FilterSidebar
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onReset={handleResetFilters}
          facets={facets}
          isCollapsed={isFilterCollapsed}
          onToggleCollapse={() => setIsFilterCollapsed(!isFilterCollapsed)}
        />

        {/* Main content */}
        <div className="flex-1 min-w-0">
          {/* Search and quick filters */}
          <div className="space-y-4 mb-6">
            <PatientSearchInput
              value={searchQuery}
              onChange={handleSearch}
              className="max-w-xl"
            />

            {/* Quick filters */}
            <div className="flex items-center gap-2 flex-wrap">
              {QUICK_FILTERS.map((filter) => (
                <button
                  key={filter.id}
                  onClick={() => handleQuickFilter(filter)}
                  className={`
                    px-3 py-1.5 text-sm rounded-full border transition-colors
                    ${
                      activeQuickFilter === filter.id
                        ? "bg-primary text-primary-foreground border-primary"
                        : "hover:bg-muted border-input"
                    }
                  `}
                >
                  {filter.label}
                </button>
              ))}

              {/* Results count */}
              <div className="ml-auto text-sm text-muted-foreground">
                {isLoading ? (
                  "Loading..."
                ) : (
                  <>
                    Showing {(currentPage - 1) * 20 + 1}-
                    {Math.min(currentPage * 20, totalCount)} of{" "}
                    {totalCount.toLocaleString()} patients
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Patient table */}
          <PatientTable
            patients={patients}
            sortBy={sortBy}
            sortDirection={sortDirection}
            onSort={handleSort}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            onRowClick={handleRowClick}
            isLoading={isLoading}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-6 flex justify-center">
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={handlePageChange}
                showFirstLast
              />
            </div>
          )}
        </div>
      </div>

      {/* Bulk actions bar */}
      <BulkActionsBar
        selectedCount={selectedIds.length}
        onExport={handleBulkExport}
        onArchive={handleBulkArchive}
        onActivate={handleBulkActivate}
        onDelete={handleBulkDelete}
        onClearSelection={() => setSelectedIds([])}
        isLoading={isPending}
      />
    </DashboardLayout>
  );
}
