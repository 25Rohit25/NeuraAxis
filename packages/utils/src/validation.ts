import { z } from "zod";

/**
 * Validate email address
 */
export function isValidEmail(email: string): boolean {
    const emailSchema = z.string().email();
    return emailSchema.safeParse(email).success;
}

/**
 * Validate phone number (basic US format)
 */
export function isValidPhone(phone: string): boolean {
    const phoneRegex = /^\+?1?\s*\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$/;
    return phoneRegex.test(phone);
}

/**
 * Validate date string (ISO format)
 */
export function isValidDate(date: string): boolean {
    const dateSchema = z.string().datetime();
    return dateSchema.safeParse(date).success;
}

/**
 * Validate UUID
 */
export function isValidUUID(uuid: string): boolean {
    const uuidSchema = z.string().uuid();
    return uuidSchema.safeParse(uuid).success;
}

/**
 * Validate URL
 */
export function isValidURL(url: string): boolean {
    const urlSchema = z.string().url();
    return urlSchema.safeParse(url).success;
}

/**
 * Validate password strength
 */
export function validatePassword(password: string): {
    isValid: boolean;
    errors: string[];
} {
    const errors: string[] = [];

    if (password.length < 8) {
        errors.push("Password must be at least 8 characters long");
    }
    if (!/[A-Z]/.test(password)) {
        errors.push("Password must contain at least one uppercase letter");
    }
    if (!/[a-z]/.test(password)) {
        errors.push("Password must contain at least one lowercase letter");
    }
    if (!/[0-9]/.test(password)) {
        errors.push("Password must contain at least one number");
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        errors.push("Password must contain at least one special character");
    }

    return {
        isValid: errors.length === 0,
        errors,
    };
}

/** Medical Record Number validation schemas */
export const mrnSchema = z
    .string()
    .min(6)
    .max(20)
    .regex(/^[A-Z0-9-]+$/);

/**
 * Validate Medical Record Number
 */
export function isValidMRN(mrn: string): boolean {
    return mrnSchema.safeParse(mrn).success;
}

/**
 * Validate ICD-10 code format
 */
export function isValidICD10(code: string): boolean {
    // ICD-10 format: Letter + 2 digits + optional decimal + up to 4 more characters
    const icd10Regex = /^[A-Z][0-9]{2}(\.[A-Z0-9]{1,4})?$/i;
    return icd10Regex.test(code);
}
