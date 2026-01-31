/**
 * NEURAXIS - Patient Table Component
 * Data table with sorting, selection, and actions
 */

"use client";

import { cn, formatDate } from "@/lib/utils";
import type {
  PatientListItem,
  PatientTableColumn,
  SortDirection,
  SortField,
} from "@/types/patient-search";
import Link from "next/link";
import { useState } from "react";

interface PatientTableProps {
  patients: PatientListItem[];
  columns?: PatientTableColumn[];
  sortBy?: SortField;
  sortDirection?: SortDirection;
  onSort?: (field: SortField, direction: SortDirection) => void;
  selectedIds?: string[];
  onSelectionChange?: (ids: string[]) => void;
  onRowClick?: (patient: PatientListItem) => void;
  isLoading?: boolean;
  className?: string;
}

const STATUS_STYLES: Record<string, { bg: string; text: string }> = {
  active: { bg: "bg-success/10", text: "text-success" },
  inactive: { bg: "bg-muted", text: "text-muted-foreground" },
  deceased: { bg: "bg-danger/10", text: "text-danger" },
  transferred: { bg: "bg-warning/10", text: "text-warning" },
};

const GENDER_LABELS: Record<string, string> = {
  male: "Male",
  female: "Female",
  other: "Other",
  prefer_not_to_say: "N/A",
};

export function PatientTable({
  patients,
  columns,
  sortBy = "createdAt",
  sortDirection = "desc",
  onSort,
  selectedIds = [],
  onSelectionChange,
  onRowClick,
  isLoading = false,
  className,
}: PatientTableProps) {
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  const defaultColumns: PatientTableColumn[] = [
    { key: "select", label: "", width: "40px", align: "center" },
    { key: "mrn", label: "MRN", sortable: true, width: "120px" },
    { key: "fullName", label: "Patient Name", sortable: true },
    {
      key: "age",
      label: "Age",
      sortable: true,
      width: "60px",
      align: "center",
    },
    { key: "gender", label: "Gender", width: "80px" },
    { key: "phonePrimary", label: "Phone", width: "130px" },
    { key: "status", label: "Status", width: "100px" },
    {
      key: "lastVisitDate",
      label: "Last Visit",
      sortable: true,
      width: "110px",
    },
    { key: "createdAt", label: "Registered", sortable: true, width: "110px" },
    { key: "actions", label: "", width: "80px", align: "right" },
  ];

  const displayColumns = columns || defaultColumns;

  const allSelected =
    patients.length > 0 && selectedIds.length === patients.length;
  const someSelected =
    selectedIds.length > 0 && selectedIds.length < patients.length;

  const handleSelectAll = () => {
    if (allSelected) {
      onSelectionChange?.([]);
    } else {
      onSelectionChange?.(patients.map((p) => p.id));
    }
  };

  const handleSelectOne = (id: string) => {
    if (selectedIds.includes(id)) {
      onSelectionChange?.(selectedIds.filter((sid) => sid !== id));
    } else {
      onSelectionChange?.([...selectedIds, id]);
    }
  };

  const handleSort = (field: SortField) => {
    if (!onSort) return;
    if (sortBy === field) {
      onSort(field, sortDirection === "asc" ? "desc" : "asc");
    } else {
      onSort(field, "asc");
    }
  };

  const getSortIcon = (field: string) => {
    if (sortBy !== field) return null;
    return sortDirection === "asc" ? (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="m18 15-6-6-6 6" />
      </svg>
    ) : (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="m6 9 6 6 6-6" />
      </svg>
    );
  };

  const renderCell = (patient: PatientListItem, column: PatientTableColumn) => {
    switch (column.key) {
      case "select":
        return (
          <input
            type="checkbox"
            checked={selectedIds.includes(patient.id)}
            onChange={(e) => {
              e.stopPropagation();
              handleSelectOne(patient.id);
            }}
            className="rounded border-input text-primary focus:ring-primary"
            aria-label={`Select ${patient.fullName}`}
          />
        );

      case "mrn":
        return (
          <span className="font-mono text-xs text-muted-foreground">
            {patient.mrn}
          </span>
        );

      case "fullName":
        return (
          <div className="flex items-center gap-3">
            {/* Avatar */}
            <div className="h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-medium">
              {patient.firstName[0]}
              {patient.lastName[0]}
            </div>
            <div>
              <p className="font-medium text-sm">{patient.fullName}</p>
              {patient.email && (
                <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                  {patient.email}
                </p>
              )}
            </div>
          </div>
        );

      case "age":
        return <span className="text-sm">{patient.age}</span>;

      case "gender":
        return (
          <span className="text-sm text-muted-foreground">
            {GENDER_LABELS[patient.gender] || patient.gender}
          </span>
        );

      case "phonePrimary":
        return (
          <span className="text-sm text-muted-foreground">
            {patient.phonePrimary}
          </span>
        );

      case "status":
        const style = STATUS_STYLES[patient.status] || STATUS_STYLES.inactive;
        return (
          <span
            className={cn(
              "inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize",
              style.bg,
              style.text
            )}
          >
            {patient.status}
          </span>
        );

      case "lastVisitDate":
        return (
          <span className="text-sm text-muted-foreground">
            {patient.lastVisitDate ? formatDate(patient.lastVisitDate) : "—"}
          </span>
        );

      case "createdAt":
        return (
          <span className="text-sm text-muted-foreground">
            {formatDate(patient.createdAt)}
          </span>
        );

      case "actions":
        return (
          <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Link
              href={`/patients/${patient.id}`}
              className="p-1.5 rounded hover:bg-muted"
              onClick={(e) => e.stopPropagation()}
              aria-label={`View ${patient.fullName}`}
            >
              <svg
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </Link>
            <Link
              href={`/patients/${patient.id}/edit`}
              className="p-1.5 rounded hover:bg-muted"
              onClick={(e) => e.stopPropagation()}
              aria-label={`Edit ${patient.fullName}`}
            >
              <svg
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
            </Link>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={cn("border rounded-lg overflow-hidden bg-card", className)}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted/50 border-b">
            <tr>
              {displayColumns.map((column) => (
                <th
                  key={column.key}
                  className={cn(
                    "px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider",
                    column.align === "center" && "text-center",
                    column.align === "right" && "text-right",
                    column.sortable &&
                      "cursor-pointer hover:text-foreground select-none"
                  )}
                  style={{ width: column.width }}
                  onClick={() =>
                    column.sortable && handleSort(column.key as SortField)
                  }
                >
                  {column.key === "select" ? (
                    <input
                      type="checkbox"
                      checked={allSelected}
                      ref={(el) => el && (el.indeterminate = someSelected)}
                      onChange={handleSelectAll}
                      className="rounded border-input text-primary focus:ring-primary"
                      aria-label="Select all patients"
                    />
                  ) : (
                    <div className="flex items-center gap-1">
                      {column.label}
                      {column.sortable && getSortIcon(column.key)}
                    </div>
                  )}
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="divide-y">
            {isLoading ? (
              // Loading skeleton
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  {displayColumns.map((col) => (
                    <td key={col.key} className="px-4 py-3">
                      <div className="h-4 bg-muted rounded" />
                    </td>
                  ))}
                </tr>
              ))
            ) : patients.length === 0 ? (
              // Empty state
              <tr>
                <td
                  colSpan={displayColumns.length}
                  className="px-4 py-16 text-center"
                >
                  <div className="flex flex-col items-center">
                    <svg
                      className="h-12 w-12 text-muted-foreground/50 mb-4"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                    >
                      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                      <circle cx="9" cy="7" r="4" />
                      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                    </svg>
                    <p className="text-muted-foreground font-medium mb-1">
                      No patients found
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Try adjusting your search or filters
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              // Patient rows
              patients.map((patient) => (
                <tr
                  key={patient.id}
                  onClick={() => onRowClick?.(patient)}
                  onMouseEnter={() => setHoveredRow(patient.id)}
                  onMouseLeave={() => setHoveredRow(null)}
                  className={cn(
                    "group transition-colors",
                    onRowClick && "cursor-pointer",
                    selectedIds.includes(patient.id) && "bg-primary/5",
                    hoveredRow === patient.id && "bg-muted/50"
                  )}
                >
                  {displayColumns.map((column) => (
                    <td
                      key={column.key}
                      className={cn(
                        "px-4 py-3",
                        column.align === "center" && "text-center",
                        column.align === "right" && "text-right"
                      )}
                    >
                      {renderCell(patient, column)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default PatientTable;
