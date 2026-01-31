import { format, parseISO, isValid, formatDistanceToNow } from "date-fns";

/**
 * Format a date string or Date object
 */
export function formatDate(
    date: string | Date,
    formatStr: string = "PPP"
): string {
    const dateObj = typeof date === "string" ? parseISO(date) : date;
    if (!isValid(dateObj)) {
        return "Invalid date";
    }
    return format(dateObj, formatStr);
}

/**
 * Format a date as relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date): string {
    const dateObj = typeof date === "string" ? parseISO(date) : date;
    if (!isValid(dateObj)) {
        return "Invalid date";
    }
    return formatDistanceToNow(dateObj, { addSuffix: true });
}

/**
 * Format a number with locale-specific formatting
 */
export function formatNumber(
    value: number,
    options: Intl.NumberFormatOptions = {}
): string {
    return new Intl.NumberFormat("en-US", options).format(value);
}

/**
 * Format a number as currency
 */
export function formatCurrency(
    value: number,
    currency: string = "USD"
): string {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency,
    }).format(value);
}

/**
 * Format a percentage
 */
export function formatPercentage(value: number, decimals: number = 1): string {
    return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format file size in human-readable format
 */
export function formatFileSize(bytes: number): string {
    const units = ["B", "KB", "MB", "GB", "TB"];
    let unitIndex = 0;
    let size = bytes;

    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * Truncate a string to a maximum length
 */
export function truncate(str: string, maxLength: number): string {
    if (str.length <= maxLength) {
        return str;
    }
    return `${str.slice(0, maxLength - 3)}...`;
}

/**
 * Capitalize the first letter of a string
 */
export function capitalize(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Convert string to title case
 */
export function toTitleCase(str: string): string {
    return str
        .split(" ")
        .map((word) => capitalize(word))
        .join(" ");
}
