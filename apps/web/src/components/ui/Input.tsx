/**
 * NEURAXIS - Input Component with Validation States
 * Accessible form input with label, error states, and character count
 */

import { cn } from "@/lib/utils";
import React, { forwardRef, useId } from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  isSuccess?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type = "text",
      label,
      error,
      hint,
      leftIcon,
      rightIcon,
      isSuccess,
      id,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const inputId = id || generatedId;
    const errorId = `${inputId}-error`;
    const hintId = `${inputId}-hint`;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="mb-1.5 block text-sm font-medium text-foreground"
          >
            {label}
            {props.required && <span className="ml-1 text-danger">*</span>}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-muted-foreground">
              {leftIcon}
            </div>
          )}
          <input
            type={type}
            id={inputId}
            ref={ref}
            aria-invalid={!!error}
            aria-describedby={error ? errorId : hint ? hintId : undefined}
            className={cn(
              `flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm
               ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium
               placeholder:text-muted-foreground transition-colors duration-200
               focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
               disabled:cursor-not-allowed disabled:opacity-50`,
              leftIcon && "pl-10",
              rightIcon && "pr-10",
              error && "border-danger focus-visible:ring-danger",
              isSuccess &&
                !error &&
                "border-success focus-visible:ring-success",
              !error && !isSuccess && "border-input",
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p id={errorId} className="mt-1.5 text-sm text-danger" role="alert">
            {error}
          </p>
        )}
        {hint && !error && (
          <p id={hintId} className="mt-1.5 text-sm text-muted-foreground">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };

/**
 * TextArea with character count
 */
export interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
  maxLength?: number;
  showCharacterCount?: boolean;
}

const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  (
    {
      className,
      label,
      error,
      hint,
      maxLength,
      showCharacterCount = false,
      id,
      value,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const textareaId = id || generatedId;
    const errorId = `${textareaId}-error`;
    const hintId = `${textareaId}-hint`;
    const charCount = typeof value === "string" ? value.length : 0;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={textareaId}
            className="mb-1.5 block text-sm font-medium text-foreground"
          >
            {label}
            {props.required && <span className="ml-1 text-danger">*</span>}
          </label>
        )}
        <div className="relative">
          <textarea
            id={textareaId}
            ref={ref}
            value={value}
            maxLength={maxLength}
            aria-invalid={!!error}
            aria-describedby={error ? errorId : hint ? hintId : undefined}
            className={cn(
              `flex min-h-[80px] w-full rounded-md border bg-background px-3 py-2 text-sm
               ring-offset-background placeholder:text-muted-foreground transition-colors duration-200
               focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
               disabled:cursor-not-allowed disabled:opacity-50 resize-y`,
              error && "border-danger focus-visible:ring-danger",
              !error && "border-input",
              className
            )}
            {...props}
          />
        </div>
        <div className="mt-1.5 flex justify-between">
          <div>
            {error && (
              <p id={errorId} className="text-sm text-danger" role="alert">
                {error}
              </p>
            )}
            {hint && !error && (
              <p id={hintId} className="text-sm text-muted-foreground">
                {hint}
              </p>
            )}
          </div>
          {showCharacterCount && maxLength && (
            <span
              className={cn(
                "text-sm",
                charCount >= maxLength ? "text-danger" : "text-muted-foreground"
              )}
            >
              {charCount}/{maxLength}
            </span>
          )}
        </div>
      </div>
    );
  }
);

TextArea.displayName = "TextArea";

export { TextArea };

/**
 * FormField wrapper component
 */
export interface FormFieldProps {
  label: string;
  htmlFor?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
  className?: string;
}

export function FormField({
  label,
  htmlFor,
  error,
  hint,
  required,
  children,
  className,
}: FormFieldProps) {
  const generatedId = useId();
  const fieldId = htmlFor || generatedId;

  return (
    <div className={cn("space-y-1.5", className)}>
      <label
        htmlFor={fieldId}
        className="block text-sm font-medium text-foreground"
      >
        {label}
        {required && <span className="ml-1 text-danger">*</span>}
      </label>
      {children}
      {error && (
        <p className="text-sm text-danger" role="alert">
          {error}
        </p>
      )}
      {hint && !error && (
        <p className="text-sm text-muted-foreground">{hint}</p>
      )}
    </div>
  );
}
