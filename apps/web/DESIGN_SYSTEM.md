# NEURAXIS Design System

A comprehensive, accessible design system for medical diagnosis platforms built with React, Tailwind CSS, and TypeScript.

## Features

- 🏥 **Medical-focused components** - Patient cards, diagnosis displays, case management
- ♿ **WCAG 2.1 AA Compliant** - Full accessibility support with ARIA attributes
- 📱 **Mobile-first responsive** - Works on all device sizes
- 🌙 **Dark mode support** - System preference detection and manual toggle
- ⏳ **Loading states** - Skeleton components for every data display
- 🎨 **Professional aesthetics** - Blue/white medical color scheme

## Installation

```bash
# Install dependencies
npm install

# Run Storybook to view components
npm run storybook
```

## Components

### Layout Components

- `AuthLayout` - Full-page auth layout with branding
- `DashboardLayout` - Sidebar navigation with header
- `PageHeader` - Page title with breadcrumbs and actions

### UI Components

- `Button` - Primary, secondary, danger, ghost, outline, link variants
- `Alert` - Info, success, warning, error notifications
- `Input` / `TextArea` - Form inputs with validation states
- `FormField` - Wrapper with label and error handling
- `Select` - Searchable dropdown
- `DatePicker` - Calendar date selector
- `FileUpload` - Drag-drop file upload with progress
- `Modal` / `ConfirmDialog` - Accessible dialogs
- `Toast` - Notification system
- `Tabs` - Default, pills, underline variants
- `Breadcrumbs` - Navigation breadcrumbs
- `Pagination` - Page navigation with ellipsis
- `Table` - Sortable, filterable data table
- `Skeleton` - Loading state placeholders

### Medical Components

- `PatientCard` - Patient summary with avatar and status
- `CaseCard` - Medical case overview with priority
- `DiagnosisCard` - AI diagnosis with confidence meter
- `TimelineCard` - Patient history timeline

## Usage

```tsx
import { Button, PatientCard, Alert } from "@/components";

function PatientList() {
  return (
    <>
      <Alert variant="info" title="Notice">
        Review pending lab results
      </Alert>

      <PatientCard
        id="1"
        firstName="Sarah"
        lastName="Johnson"
        mrn="MRN-001234"
        dateOfBirth="1985-03-15"
        gender="female"
        status="active"
        onClick={() => console.log("View patient")}
      />

      <Button variant="primary">Add Patient</Button>
    </>
  );
}
```

## Theming

The design system uses CSS custom properties for theming. Customize colors in `globals.css`:

```css
:root {
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  /* ... */
}

.dark {
  --primary: 217.2 91.2% 59.8%;
  /* ... */
}
```

## Color System

| Color   | Light Mode    | Dark Mode     | Usage                        |
| ------- | ------------- | ------------- | ---------------------------- |
| Primary | Blue #2563eb  | Blue #3b82f6  | Buttons, links, focus states |
| Accent  | Cyan #06b6d4  | Cyan #0891b2  | AI features, highlights      |
| Success | Green #22c55e | Green #22c55e | Positive states              |
| Warning | Amber #f59e0b | Amber #f59e0b | Caution states               |
| Danger  | Red #ef4444   | Red #ef4444   | Errors, critical             |

### Medical Severity Colors

- `minimal` - Green
- `mild` - Lime
- `moderate` - Amber
- `severe` - Orange
- `critical` - Red

## Accessibility

All components follow WCAG 2.1 AA guidelines:

- Keyboard navigation support
- ARIA labels and roles
- Focus management in modals
- Color contrast ratios ≥ 4.5:1
- Reduced motion preference support
- Skip links for screen readers

## File Structure

```
src/
├── app/
│   └── globals.css          # Global styles and CSS variables
├── components/
│   ├── index.ts             # Central exports
│   ├── layout/
│   │   └── Layout.tsx       # Auth, Dashboard, PageHeader
│   ├── medical/
│   │   └── Cards.tsx        # Medical-specific cards
│   └── ui/
│       ├── Alert.tsx
│       ├── Button.tsx
│       ├── FileUpload.tsx
│       ├── Input.tsx
│       ├── Modal.tsx
│       ├── Navigation.tsx
│       ├── Select.tsx
│       ├── Skeleton.tsx
│       ├── Table.tsx
│       └── Toast.tsx
├── lib/
│   └── utils.ts             # Utility functions
└── providers/
    └── ThemeProvider.tsx    # Dark mode provider
```

## Storybook

View all components and their variants in Storybook:

```bash
npm run storybook
```

This opens Storybook at http://localhost:6006 with:

- Interactive component playground
- Accessibility checks (a11y addon)
- Dark/light mode toggle
- Auto-generated documentation

## Dependencies

- `react` - UI framework
- `tailwindcss` - Styling
- `class-variance-authority` - Component variants
- `clsx` + `tailwind-merge` - Class name utilities
- `@storybook/react` - Component documentation

## License

MIT © NEURAXIS
