/**
 * NEURAXIS Design System - Component Exports
 * Central export file for all UI components
 */

// UI Components
export { Alert, alertVariants, type AlertProps } from "./ui/Alert";
export { Button, buttonVariants, type ButtonProps } from "./ui/Button";
export {
  FileList,
  FileUpload,
  type FileItem,
  type FileListProps,
  type FileUploadProps,
} from "./ui/FileUpload";
export {
  FormField,
  Input,
  TextArea,
  type FormFieldProps,
  type InputProps,
  type TextAreaProps,
} from "./ui/Input";
export {
  ConfirmDialog,
  Modal,
  type ConfirmDialogProps,
  type ModalProps,
} from "./ui/Modal";
export {
  Breadcrumbs,
  PageInfo,
  Pagination,
  TabPanel,
  Tabs,
  type BreadcrumbsProps,
  type PaginationProps,
  type TabsProps,
} from "./ui/Navigation";
export {
  DatePicker,
  Select,
  type DatePickerProps,
  type SelectOption,
  type SelectProps,
} from "./ui/Select";
export {
  SkeletonTable,
  Table,
  type Column,
  type SkeletonTableProps,
  type TableProps,
} from "./ui/Table";
export { ToastProvider, useToast } from "./ui/Toast";

// Layout Components
export { AuthLayout, DashboardLayout, PageHeader } from "./layout/Layout";

// Medical Components
export {
  CaseCard,
  DiagnosisCard,
  PatientCard,
  TimelineCard,
} from "./medical/Cards";
export type {
  CaseCardProps,
  DiagnosisCardProps,
  PatientCardProps,
  TimelineCardProps,
  TimelineEvent,
} from "./medical/Cards";
