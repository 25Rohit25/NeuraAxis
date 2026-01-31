import * as React from "react";
import { cn } from "../lib/utils";

export interface InputProps
    extends React.InputHTMLAttributes<HTMLInputElement> {
    error?: boolean;
    icon?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
    ({ className, type, error, icon, ...props }, ref) => {
        return (
            <div className="relative">
                {icon && (
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                        {icon}
                    </div>
                )}
                <input
                    type={type}
                    className={cn(
                        "flex h-11 w-full rounded-xl border bg-white px-4 py-2 text-sm transition-all duration-200",
                        "border-slate-200 dark:border-slate-700 dark:bg-slate-800",
                        "text-slate-900 dark:text-white placeholder:text-slate-400",
                        "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                        "disabled:cursor-not-allowed disabled:opacity-50",
                        error && "border-red-500 focus:ring-red-500",
                        icon && "pl-12",
                        className
                    )}
                    ref={ref}
                    {...props}
                />
            </div>
        );
    }
);
Input.displayName = "Input";

export { Input };
