/**
 * NEURAXIS - Data Table Component
 * Sortable, filterable table with pagination and loading states
 */

"use client";

import { cn } from "@/lib/utils";
import React from "react";
import { Pagination } from "./Navigation";

// ============================================================================
// TYPES
// ============================================================================

export type SortDirection = "asc" | "desc" | null;

export interface Column<T> {
  key: keyof T | string;
  header: string;
  sortable?: boolean;
  width?: string;
  align?: "left" | "center" | "right";
  render?: (value: any, row: T, index: number) => React.ReactNode;
  className?: string;
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyField: keyof T;
  sortable?: boolean;
  selectable?: boolean;
  selectedRows?: Set<string>;
  onSelectionChange?: (selected: Set<string>) => void;
  onRowClick?: (row: T) => void;
  sortColumn?: string;
  sortDirection?: SortDirection;
  onSort?: (column: string, direction: SortDirection) => void;
  pagination?: {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
  };
  isLoading?: boolean;
  emptyMessage?: string;
  className?: string;
}

// ============================================================================
// TABLE COMPONENT
// ============================================================================

export function Table<T extends Record<string, any>>({
  columns,
  data,
  keyField,
  sortable = false,
  selectable = false,
  selectedRows,
  onSelectionChange,
  onRowClick,
  sortColumn,
  sortDirection,
  onSort,
  pagination,
  isLoading = false,
  emptyMessage = "No data available",
  className,
}: TableProps<T>) {
  // Handle column header click for sorting
  const handleHeaderClick = (column: Column<T>) => {
    if (!sortable || !column.sortable || !onSort) return;

    const key = column.key as string;
    let newDirection: SortDirection = "asc";

    if (sortColumn === key) {
      newDirection =
        sortDirection === "asc"
          ? "desc"
          : sortDirection === "desc"
            ? null
            : "asc";
    }

    onSort(key, newDirection);
  };

  // Handle row selection
  const handleSelectAll = () => {
    if (!selectedRows || !onSelectionChange) return;

    if (selectedRows.size === data.length) {
      onSelectionChange(new Set());
    } else {
      onSelectionChange(new Set(data.map((row) => String(row[keyField]))));
    }
  };

  const handleSelectRow = (rowKey: string) => {
    if (!selectedRows || !onSelectionChange) return;

    const newSelected = new Set(selectedRows);
    if (newSelected.has(rowKey)) {
      newSelected.delete(rowKey);
    } else {
      newSelected.add(rowKey);
    }
    onSelectionChange(newSelected);
  };

  // Get cell value
  const getCellValue = (row: T, column: Column<T>, index: number) => {
    const key = column.key as keyof T;
    const value = row[key];

    if (column.render) {
      return column.render(value, row, index);
    }

    if (value === null || value === undefined) {
      return <span className="text-muted-foreground">—</span>;
    }

    return String(value);
  };

  const alignClass = {
    left: "text-left",
    center: "text-center",
    right: "text-right",
  };

  return (
    <div className={cn("w-full", className)}>
      <div className="relative overflow-x-auto rounded-lg border">
        <table className="w-full text-sm caption-bottom">
          {/* Header */}
          <thead className="bg-muted/50 border-b">
            <tr>
              {/* Selection checkbox */}
              {selectable && (
                <th className="w-12 p-3">
                  <input
                    type="checkbox"
                    checked={
                      data.length > 0 && selectedRows?.size === data.length
                    }
                    indeterminate={
                      selectedRows &&
                      selectedRows.size > 0 &&
                      selectedRows.size < data.length
                    }
                    onChange={handleSelectAll}
                    className="rounded border-input"
                    aria-label="Select all rows"
                  />
                </th>
              )}

              {columns.map((column, index) => (
                <th
                  key={String(column.key)}
                  className={cn(
                    "px-4 py-3 font-medium text-muted-foreground",
                    alignClass[column.align || "left"],
                    column.sortable &&
                      sortable &&
                      "cursor-pointer hover:text-foreground select-none",
                    column.className
                  )}
                  style={{ width: column.width }}
                  onClick={() => handleHeaderClick(column)}
                  aria-sort={
                    sortColumn === column.key
                      ? sortDirection === "asc"
                        ? "ascending"
                        : sortDirection === "desc"
                          ? "descending"
                          : undefined
                      : undefined
                  }
                >
                  <div className="flex items-center gap-1">
                    <span>{column.header}</span>
                    {column.sortable && sortable && (
                      <span className="ml-1">
                        {sortColumn === column.key ? (
                          sortDirection === "asc" ? (
                            <svg
                              className="h-4 w-4"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <path d="m18 15-6-6-6 6" />
                            </svg>
                          ) : sortDirection === "desc" ? (
                            <svg
                              className="h-4 w-4"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <path d="m6 9 6 6 6-6" />
                            </svg>
                          ) : (
                            <svg
                              className="h-4 w-4 text-muted-foreground/50"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <path d="m7 15 5 5 5-5M7 9l5-5 5 5" />
                            </svg>
                          )
                        ) : (
                          <svg
                            className="h-4 w-4 text-muted-foreground/50"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <path d="m7 15 5 5 5-5M7 9l5-5 5 5" />
                          </svg>
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          {/* Body */}
          <tbody>
            {isLoading ? (
              // Loading skeleton
              Array.from({ length: 5 }).map((_, index) => (
                <tr key={index} className="border-b">
                  {selectable && (
                    <td className="p-3">
                      <div className="h-4 w-4 rounded bg-muted animate-pulse" />
                    </td>
                  )}
                  {columns.map((column, colIndex) => (
                    <td key={colIndex} className="px-4 py-3">
                      <div
                        className="h-4 rounded bg-muted animate-pulse"
                        style={{ width: `${60 + Math.random() * 40}%` }}
                      />
                    </td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              // Empty state
              <tr>
                <td
                  colSpan={columns.length + (selectable ? 1 : 0)}
                  className="px-4 py-12 text-center text-muted-foreground"
                >
                  <div className="flex flex-col items-center gap-2">
                    <svg
                      className="h-12 w-12 text-muted-foreground/30"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1"
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="9" y1="12" x2="15" y2="12" />
                      <line x1="9" y1="16" x2="15" y2="16" />
                    </svg>
                    <span>{emptyMessage}</span>
                  </div>
                </td>
              </tr>
            ) : (
              // Data rows
              data.map((row, rowIndex) => {
                const rowKey = String(row[keyField]);
                const isSelected = selectedRows?.has(rowKey);

                return (
                  <tr
                    key={rowKey}
                    onClick={() => onRowClick?.(row)}
                    className={cn(
                      "border-b transition-colors",
                      onRowClick && "cursor-pointer",
                      isSelected ? "bg-primary/5" : "hover:bg-muted/50"
                    )}
                    data-state={isSelected ? "selected" : undefined}
                  >
                    {selectable && (
                      <td className="p-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleSelectRow(rowKey)}
                          onClick={(e) => e.stopPropagation()}
                          className="rounded border-input"
                          aria-label={`Select row ${rowIndex + 1}`}
                        />
                      </td>
                    )}
                    {columns.map((column, colIndex) => (
                      <td
                        key={String(column.key)}
                        className={cn(
                          "px-4 py-3",
                          alignClass[column.align || "left"],
                          column.className
                        )}
                      >
                        {getCellValue(row, column, rowIndex)}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && !isLoading && data.length > 0 && (
        <div className="mt-4 flex justify-center">
          <Pagination {...pagination} />
        </div>
      )}
    </div>
  );
}

// ============================================================================
// SKELETON TABLE
// ============================================================================

export interface SkeletonTableProps {
  columns: number;
  rows?: number;
  showHeader?: boolean;
  className?: string;
}

export function SkeletonTable({
  columns,
  rows = 5,
  showHeader = true,
  className,
}: SkeletonTableProps) {
  return (
    <div className={cn("w-full rounded-lg border overflow-hidden", className)}>
      <table className="w-full">
        {showHeader && (
          <thead className="bg-muted/50 border-b">
            <tr>
              {Array.from({ length: columns }).map((_, index) => (
                <th key={index} className="px-4 py-3">
                  <div
                    className="h-4 rounded bg-muted animate-pulse"
                    style={{ width: `${40 + Math.random() * 40}%` }}
                  />
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <tr key={rowIndex} className="border-b last:border-0">
              {Array.from({ length: columns }).map((_, colIndex) => (
                <td key={colIndex} className="px-4 py-3">
                  <div
                    className="h-4 rounded bg-muted animate-pulse"
                    style={{
                      width: `${50 + Math.random() * 50}%`,
                      animationDelay: `${(rowIndex * columns + colIndex) * 50}ms`,
                    }}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
