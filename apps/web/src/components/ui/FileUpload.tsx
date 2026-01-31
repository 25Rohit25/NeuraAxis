/**
 * NEURAXIS - File Upload Component
 * Drag-drop file upload with progress and validation
 */

"use client";

import { cn } from "@/lib/utils";
import React, { useCallback, useRef, useState } from "react";

export interface FileUploadProps {
  accept?: string;
  maxSize?: number; // in bytes
  maxFiles?: number;
  multiple?: boolean;
  disabled?: boolean;
  onFilesSelected: (files: File[]) => void;
  onUploadProgress?: (progress: number) => void;
  onError?: (error: string) => void;
  className?: string;
  label?: string;
  hint?: string;
}

export function FileUpload({
  accept,
  maxSize = 10 * 1024 * 1024, // 10MB default
  maxFiles = 5,
  multiple = false,
  disabled = false,
  onFilesSelected,
  onUploadProgress,
  onError,
  className,
  label = "Upload files",
  hint,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFiles = useCallback(
    (files: File[]): { valid: File[]; errors: string[] } => {
      const valid: File[] = [];
      const errors: string[] = [];

      if (files.length > maxFiles) {
        errors.push(`Maximum ${maxFiles} files allowed`);
        files = files.slice(0, maxFiles);
      }

      files.forEach((file) => {
        if (maxSize && file.size > maxSize) {
          errors.push(
            `${file.name} exceeds maximum size of ${formatBytes(maxSize)}`
          );
          return;
        }

        if (accept) {
          const acceptedTypes = accept.split(",").map((t) => t.trim());
          const fileExtension = `.${file.name.split(".").pop()?.toLowerCase()}`;
          const isAccepted = acceptedTypes.some(
            (type) =>
              type === file.type ||
              type === fileExtension ||
              (type.endsWith("/*") &&
                file.type.startsWith(type.replace("/*", "")))
          );

          if (!isAccepted) {
            errors.push(`${file.name} is not an accepted file type`);
            return;
          }
        }

        valid.push(file);
      });

      return { valid, errors };
    },
    [accept, maxSize, maxFiles]
  );

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;

      const fileArray = Array.from(files);
      const { valid, errors } = validateFiles(fileArray);

      if (errors.length > 0 && onError) {
        onError(errors.join(". "));
      }

      if (valid.length > 0) {
        onFilesSelected(valid);
      }
    },
    [validateFiles, onFilesSelected, onError]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;
    handleFiles(e.dataTransfer.files);
  };

  const handleClick = () => {
    if (!disabled) inputRef.current?.click();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
    // Reset input value to allow selecting the same file again
    e.target.value = "";
  };

  return (
    <div className={cn("w-full", className)}>
      {label && (
        <label className="mb-1.5 block text-sm font-medium text-foreground">
          {label}
        </label>
      )}
      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-all cursor-pointer",
          isDragging && !disabled && "border-primary bg-primary/5",
          !isDragging &&
            !disabled &&
            "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50",
          disabled && "cursor-not-allowed opacity-50 bg-muted"
        )}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            handleClick();
          }
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleInputChange}
          disabled={disabled}
          className="sr-only"
          aria-label={label}
        />

        {/* Icon */}
        <div className="mb-4 rounded-full bg-muted p-3">
          <svg
            className="h-8 w-8 text-muted-foreground"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>

        <p className="mb-1 text-sm font-medium">
          <span className="text-primary">Click to upload</span> or drag and drop
        </p>
        <p className="text-xs text-muted-foreground">
          {accept ? accept.replace(/,/g, ", ") : "Any file type"}
          {maxSize && ` (max ${formatBytes(maxSize)})`}
        </p>

        {/* Upload progress */}
        {uploadProgress !== null && (
          <div className="mt-4 w-full max-w-xs">
            <div className="mb-1 flex justify-between text-xs">
              <span>Uploading...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {hint && <p className="mt-1.5 text-sm text-muted-foreground">{hint}</p>}
    </div>
  );
}

// ============================================================================
// FILE LIST
// ============================================================================

export interface FileItem {
  file: File;
  progress?: number;
  error?: string;
  uploaded?: boolean;
}

export interface FileListProps {
  files: FileItem[];
  onRemove: (index: number) => void;
  className?: string;
}

export function FileList({ files, onRemove, className }: FileListProps) {
  if (files.length === 0) return null;

  return (
    <ul className={cn("space-y-2", className)}>
      {files.map((item, index) => (
        <li
          key={`${item.file.name}-${index}`}
          className={cn(
            "flex items-center gap-3 rounded-lg border p-3",
            item.error && "border-danger bg-danger/5",
            item.uploaded && "border-success bg-success/5"
          )}
        >
          {/* File icon */}
          <div className="shrink-0">{getFileIcon(item.file.type)}</div>

          {/* File info */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{item.file.name}</p>
            <p className="text-xs text-muted-foreground">
              {formatBytes(item.file.size)}
            </p>

            {/* Progress bar */}
            {item.progress !== undefined &&
              item.progress < 100 &&
              !item.error && (
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
              )}

            {/* Error message */}
            {item.error && (
              <p className="mt-1 text-xs text-danger">{item.error}</p>
            )}
          </div>

          {/* Status / Remove button */}
          <div className="shrink-0">
            {item.uploaded ? (
              <svg
                className="h-5 w-5 text-success"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
            ) : (
              <button
                onClick={() => onRemove(index)}
                className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                aria-label={`Remove ${item.file.name}`}
              >
                <svg
                  className="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M18 6 6 18M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

// ============================================================================
// UTILITIES
// ============================================================================

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function getFileIcon(mimeType: string): React.ReactNode {
  if (mimeType.startsWith("image/")) {
    return (
      <svg
        className="h-8 w-8 text-indigo-500"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      >
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <circle cx="9" cy="9" r="2" />
        <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
      </svg>
    );
  }
  if (mimeType.startsWith("video/")) {
    return (
      <svg
        className="h-8 w-8 text-pink-500"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      >
        <polygon points="23 7 16 12 23 17 23 7" />
        <rect x="1" y="5" width="15" height="14" rx="2" />
      </svg>
    );
  }
  if (mimeType === "application/pdf") {
    return (
      <svg
        className="h-8 w-8 text-red-500"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      >
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    );
  }
  // Default file icon
  return (
    <svg
      className="h-8 w-8 text-muted-foreground"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  );
}
