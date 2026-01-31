/**
 * NEURAXIS - Navigation Components
 * Sidebar, Breadcrumbs, Tabs, Pagination
 */

"use client";

import { cn } from "@/lib/utils";
import Link from "next/link";
import React from "react";

// ============================================================================
// BREADCRUMBS
// ============================================================================

export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ReactNode;
}

export interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  separator?: "chevron" | "slash";
  className?: string;
}

export function Breadcrumbs({
  items,
  separator = "chevron",
  className,
}: BreadcrumbsProps) {
  const separatorIcon =
    separator === "chevron" ? (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <polyline points="9 18 15 12 9 6" />
      </svg>
    ) : (
      <span>/</span>
    );

  return (
    <nav aria-label="Breadcrumb" className={className}>
      <ol className="flex items-center flex-wrap gap-1 text-sm">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li key={index} className="flex items-center gap-1">
              {index > 0 && (
                <span className="text-muted-foreground mx-1">
                  {separatorIcon}
                </span>
              )}
              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {item.icon}
                  <span>{item.label}</span>
                </Link>
              ) : (
                <span
                  className={cn(
                    "flex items-center gap-1",
                    isLast
                      ? "text-foreground font-medium"
                      : "text-muted-foreground"
                  )}
                  aria-current={isLast ? "page" : undefined}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// ============================================================================
// TABS
// ============================================================================

export interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
  badge?: string | number;
  disabled?: boolean;
}

export interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  variant?: "default" | "pills" | "underline";
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function Tabs({
  tabs,
  activeTab,
  onTabChange,
  variant = "default",
  size = "md",
  className,
}: TabsProps) {
  const baseStyles =
    "inline-flex items-center justify-center gap-2 font-medium transition-all";

  const sizeStyles = {
    sm: "text-xs px-2.5 py-1.5",
    md: "text-sm px-3 py-2",
    lg: "text-base px-4 py-2.5",
  };

  const variantStyles = {
    default: {
      container: "bg-muted p-1 rounded-lg",
      tab: "rounded-md",
      active: "bg-background text-foreground shadow-sm",
      inactive: "text-muted-foreground hover:text-foreground",
    },
    pills: {
      container: "gap-2",
      tab: "rounded-full",
      active: "bg-primary text-primary-foreground",
      inactive:
        "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground",
    },
    underline: {
      container: "border-b gap-0",
      tab: "border-b-2 -mb-px rounded-none",
      active: "border-primary text-primary",
      inactive:
        "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/30",
    },
  };

  const styles = variantStyles[variant];

  return (
    <div className={cn("flex", styles.container, className)} role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeTab === tab.id}
          aria-controls={`panel-${tab.id}`}
          tabIndex={activeTab === tab.id ? 0 : -1}
          disabled={tab.disabled}
          onClick={() => onTabChange(tab.id)}
          className={cn(
            baseStyles,
            sizeStyles[size],
            styles.tab,
            activeTab === tab.id ? styles.active : styles.inactive,
            tab.disabled && "opacity-50 cursor-not-allowed"
          )}
        >
          {tab.icon}
          <span>{tab.label}</span>
          {tab.badge !== undefined && (
            <span
              className={cn(
                "ml-1 rounded-full px-1.5 py-0.5 text-xs font-medium",
                activeTab === tab.id
                  ? "bg-primary-foreground/20"
                  : "bg-muted-foreground/20"
              )}
            >
              {tab.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

// Tab Panel component
export interface TabPanelProps {
  id: string;
  activeTab: string;
  children: React.ReactNode;
  className?: string;
}

export function TabPanel({
  id,
  activeTab,
  children,
  className,
}: TabPanelProps) {
  if (activeTab !== id) return null;

  return (
    <div
      id={`panel-${id}`}
      role="tabpanel"
      aria-labelledby={id}
      tabIndex={0}
      className={className}
    >
      {children}
    </div>
  );
}

// ============================================================================
// PAGINATION
// ============================================================================

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  showFirstLast?: boolean;
  siblingCount?: number;
  className?: string;
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  showFirstLast = true,
  siblingCount = 1,
  className,
}: PaginationProps) {
  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages: (number | "ellipsis")[] = [];

    // Always show first page
    pages.push(1);

    // Calculate range around current page
    const leftSibling = Math.max(2, currentPage - siblingCount);
    const rightSibling = Math.min(totalPages - 1, currentPage + siblingCount);

    // Add left ellipsis
    if (leftSibling > 2) {
      pages.push("ellipsis");
    }

    // Add pages around current
    for (let i = leftSibling; i <= rightSibling; i++) {
      if (i !== 1 && i !== totalPages) {
        pages.push(i);
      }
    }

    // Add right ellipsis
    if (rightSibling < totalPages - 1) {
      pages.push("ellipsis");
    }

    // Always show last page
    if (totalPages > 1) {
      pages.push(totalPages);
    }

    return pages;
  };

  const pages = getPageNumbers();

  const buttonStyles = cn(
    "inline-flex h-9 w-9 items-center justify-center rounded-md text-sm font-medium",
    "transition-colors hover:bg-muted disabled:pointer-events-none disabled:opacity-50"
  );

  return (
    <nav
      aria-label="Pagination"
      className={cn("flex items-center justify-center gap-1", className)}
    >
      {/* First page */}
      {showFirstLast && (
        <button
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
          className={buttonStyles}
          aria-label="Go to first page"
        >
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="11 17 6 12 11 7" />
            <polyline points="18 17 13 12 18 7" />
          </svg>
        </button>
      )}

      {/* Previous */}
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className={buttonStyles}
        aria-label="Go to previous page"
      >
        <svg
          className="h-4 w-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>

      {/* Page numbers */}
      {pages.map((page, index) =>
        page === "ellipsis" ? (
          <span
            key={`ellipsis-${index}`}
            className="w-9 text-center text-muted-foreground"
          >
            ...
          </span>
        ) : (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            aria-current={currentPage === page ? "page" : undefined}
            className={cn(
              buttonStyles,
              currentPage === page &&
                "bg-primary text-primary-foreground hover:bg-primary/90"
            )}
          >
            {page}
          </button>
        )
      )}

      {/* Next */}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className={buttonStyles}
        aria-label="Go to next page"
      >
        <svg
          className="h-4 w-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>

      {/* Last page */}
      {showFirstLast && (
        <button
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
          className={buttonStyles}
          aria-label="Go to last page"
        >
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="6 17 11 12 6 7" />
            <polyline points="13 17 18 12 13 7" />
          </svg>
        </button>
      )}
    </nav>
  );
}

// Compact pagination with page info
export interface PageInfoProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function PageInfo({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  className,
}: PageInfoProps) {
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  return (
    <div
      className={cn(
        "flex items-center justify-between gap-4 text-sm",
        className
      )}
    >
      <span className="text-muted-foreground">
        Showing <span className="font-medium text-foreground">{startItem}</span>{" "}
        to <span className="font-medium text-foreground">{endItem}</span> of{" "}
        <span className="font-medium text-foreground">{totalItems}</span>{" "}
        results
      </span>
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={onPageChange}
        showFirstLast={false}
      />
    </div>
  );
}
