/**
 * NEURAXIS - Textarea Component
 * Multi-line text input with variants and sizing
 */

"use client";

import { cn } from "@/lib/utils";
import React, { forwardRef } from "react";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
  resize?: "none" | "both" | "horizontal" | "vertical";
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, resize = "vertical", ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          // Base styles
          "flex min-h-[80px] w-full rounded-lg border bg-background px-3 py-2",
          "text-sm placeholder:text-muted-foreground",
          // Focus styles
          "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
          // Disabled styles
          "disabled:cursor-not-allowed disabled:opacity-50",
          // Transition
          "transition-colors duration-200",
          // Border color
          error
            ? "border-danger focus:ring-danger/30"
            : "border-input hover:border-muted-foreground/50",
          // Resize
          {
            "resize-none": resize === "none",
            resize: resize === "both",
            "resize-x": resize === "horizontal",
            "resize-y": resize === "vertical",
          },
          className
        )}
        {...props}
      />
    );
  }
);

Textarea.displayName = "Textarea";

export { Textarea };
