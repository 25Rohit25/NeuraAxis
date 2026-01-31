/**
 * Create a full API URL from base and path
 */
export function createApiUrl(basePath: string, endpoint: string): string {
    const base = basePath.endsWith("/") ? basePath.slice(0, -1) : basePath;
    const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    return `${base}${path}`;
}

/**
 * Build query string from object
 */
export function buildQueryString(
    params: Record<string, string | number | boolean | undefined>
): string {
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
            searchParams.append(key, String(value));
        }
    });

    const queryString = searchParams.toString();
    return queryString ? `?${queryString}` : "";
}

/**
 * Sleep for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Retry a function with exponential backoff
 */
export async function retryWithBackoff<T>(
    fn: () => Promise<T>,
    options: {
        maxRetries?: number;
        initialDelayMs?: number;
        maxDelayMs?: number;
        backoffMultiplier?: number;
    } = {}
): Promise<T> {
    const {
        maxRetries = 3,
        initialDelayMs = 1000,
        maxDelayMs = 30000,
        backoffMultiplier = 2,
    } = options;

    let lastError: Error | undefined;
    let delayMs = initialDelayMs;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error as Error;

            if (attempt < maxRetries) {
                await sleep(delayMs);
                delayMs = Math.min(delayMs * backoffMultiplier, maxDelayMs);
            }
        }
    }

    throw lastError;
}

/**
 * Parse API error response
 */
export function parseApiError(error: unknown): {
    message: string;
    code?: string;
    status?: number;
} {
    if (error instanceof Error) {
        return { message: error.message };
    }

    if (typeof error === "object" && error !== null) {
        const errorObj = error as Record<string, unknown>;
        return {
            message: String(errorObj.message || "An error occurred"),
            code: errorObj.code ? String(errorObj.code) : undefined,
            status: typeof errorObj.status === "number" ? errorObj.status : undefined,
        };
    }

    return { message: "An unknown error occurred" };
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
    fn: T,
    delayMs: number
): (...args: Parameters<T>) => void {
    let timeoutId: ReturnType<typeof setTimeout>;

    return (...args: Parameters<T>) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), delayMs);
    };
}

/**
 * Throttle function
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
    fn: T,
    limitMs: number
): (...args: Parameters<T>) => void {
    let lastCall = 0;

    return (...args: Parameters<T>) => {
        const now = Date.now();
        if (now - lastCall >= limitMs) {
            lastCall = now;
            fn(...args);
        }
    };
}
