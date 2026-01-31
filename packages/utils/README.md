# @neuraxis/utils

> Shared Utility Functions for NEURAXIS

## Overview

This package contains common utility functions used across NEURAXIS applications and services.

## Utilities

### Formatting
- `formatDate()` - Date formatting with locale support
- `formatCurrency()` - Currency formatting
- `formatNumber()` - Number formatting with precision

### Validation
- `isValidEmail()` - Email validation
- `isValidPhone()` - Phone number validation
- `isValidDate()` - Date validation

### Medical
- `calculateBMI()` - BMI calculation
- `parseICDCode()` - ICD code parsing
- `formatMRN()` - Medical record number formatting

### API
- `createApiUrl()` - URL construction helper
- `handleApiError()` - Error handling utility
- `retryWithBackoff()` - Retry with exponential backoff

## Usage

```typescript
import { formatDate, isValidEmail, calculateBMI } from "@neuraxis/utils";

const formattedDate = formatDate(new Date(), "PPP");
const isValid = isValidEmail("user@example.com");
const bmi = calculateBMI(70, 1.75);
```

## Development

```bash
npm run build     # Build the package
npm run test      # Run tests
npm run lint      # Lint source files
```
