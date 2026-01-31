# @neuraxis/shared-types

> Shared TypeScript Type Definitions for NEURAXIS

## Overview

This package contains all shared TypeScript types, interfaces, and enums used across NEURAXIS applications and services.

## Structure

```
src/
├── api/              # API request/response types
├── models/           # Domain model types
├── common/           # Common utility types
└── index.ts          # Main exports
```

## Usage

```typescript
import { Patient, Diagnosis, DiagnosisStatus } from "@neuraxis/shared-types";

const patient: Patient = {
  id: "123",
  name: "John Doe",
  dateOfBirth: "1990-01-01",
  // ...
};
```

## Adding New Types

1. Create the type in the appropriate subdirectory
2. Export from the subdirectory's index.ts
3. Re-export from the main index.ts

## Type Categories

### Models
- `Patient` - Patient demographic information
- `Diagnosis` - Diagnosis result with confidence scores
- `MedicalImage` - Medical imaging data
- `LabResult` - Laboratory test results

### API
- `ApiResponse<T>` - Standard API response wrapper
- `PaginatedResponse<T>` - Paginated list responses
- `ErrorResponse` - API error structure

### Common
- `ID` - Branded ID types for type safety
- `Timestamp` - Date/time handling
- `SortOrder` - Sorting parameters
