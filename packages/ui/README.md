# @neuraxis/ui

> Shared React Component Library for NEURAXIS

## Overview

This package contains reusable React components used across NEURAXIS applications. Built with accessibility in mind using Radix UI primitives.

## Components

### Core
- `Button` - Primary, secondary, and ghost button variants
- `Input` - Text input with validation states
- `Card` - Container component with glass effect option

### Feedback
- `Alert` - Success, warning, error, and info alerts
- `Toast` - Toast notification system
- `Spinner` - Loading spinner

### Layout
- `Container` - Max-width container
- `Stack` - Vertical/horizontal stack layout

### Medical-Specific
- `DiagnosisCard` - Display diagnosis results
- `PatientCard` - Patient information display
- `VitalSign` - Vital sign indicator

## Usage

```tsx
import { Button, Card, Input } from "@neuraxis/ui";

export function MyComponent() {
  return (
    <Card>
      <Input placeholder="Enter patient ID" />
      <Button variant="primary">Search</Button>
    </Card>
  );
}
```

## Development

```bash
npm run build    # Build the package
npm run lint     # Lint source files
npm run type-check  # TypeScript type checking
```
