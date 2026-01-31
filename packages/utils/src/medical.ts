/**
 * Calculate Body Mass Index (BMI)
 * @param weightKg Weight in kilograms
 * @param heightM Height in meters
 */
export function calculateBMI(weightKg: number, heightM: number): number {
    if (heightM <= 0 || weightKg <= 0) {
        throw new Error("Weight and height must be positive numbers");
    }
    return weightKg / (heightM * heightM);
}

/**
 * Get BMI category
 */
export function getBMICategory(
    bmi: number
): "underweight" | "normal" | "overweight" | "obese" {
    if (bmi < 18.5) return "underweight";
    if (bmi < 25) return "normal";
    if (bmi < 30) return "overweight";
    return "obese";
}

/**
 * Calculate age from date of birth
 */
export function calculateAge(dateOfBirth: string | Date): number {
    const dob = typeof dateOfBirth === "string" ? new Date(dateOfBirth) : dateOfBirth;
    const today = new Date();

    let age = today.getFullYear() - dob.getFullYear();
    const monthDiff = today.getMonth() - dob.getMonth();

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
        age--;
    }

    return age;
}

/**
 * Parse ICD-10 code into components
 */
export function parseICDCode(code: string): {
    category: string;
    etiology: string;
    extension?: string;
} | null {
    const match = code.match(/^([A-Z])([0-9]{2})(?:\.([A-Z0-9]{1,4}))?$/i);

    if (!match) {
        return null;
    }

    return {
        category: match[1].toUpperCase(),
        etiology: match[2],
        extension: match[3]?.toUpperCase(),
    };
}

/**
 * Format Medical Record Number (MRN)
 */
export function formatMRN(mrn: string): string {
    // Remove non-alphanumeric characters and uppercase
    const cleaned = mrn.replace(/[^A-Z0-9]/gi, "").toUpperCase();

    // Format as XXX-XXX-XXXX if long enough
    if (cleaned.length >= 10) {
        return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 6)}-${cleaned.slice(6, 10)}`;
    }

    return cleaned;
}

/**
 * Convert temperature between Fahrenheit and Celsius
 */
export function convertTemperature(
    value: number,
    from: "F" | "C",
    to: "F" | "C"
): number {
    if (from === to) return value;

    if (from === "F" && to === "C") {
        return ((value - 32) * 5) / 9;
    }

    return (value * 9) / 5 + 32;
}

/**
 * Check if vital sign is within normal range
 */
export function isVitalSignNormal(
    type: "heart_rate" | "blood_pressure_systolic" | "blood_pressure_diastolic" | "temperature" | "oxygen_saturation",
    value: number
): boolean {
    const normalRanges = {
        heart_rate: { min: 60, max: 100 },
        blood_pressure_systolic: { min: 90, max: 120 },
        blood_pressure_diastolic: { min: 60, max: 80 },
        temperature: { min: 36.1, max: 37.2 }, // Celsius
        oxygen_saturation: { min: 95, max: 100 },
    };

    const range = normalRanges[type];
    return value >= range.min && value <= range.max;
}

/**
 * Generate a diagnosis confidence label
 */
export function getConfidenceLabel(
    score: number
): "very_low" | "low" | "moderate" | "high" | "very_high" {
    if (score < 0.2) return "very_low";
    if (score < 0.4) return "low";
    if (score < 0.6) return "moderate";
    if (score < 0.8) return "high";
    return "very_high";
}
