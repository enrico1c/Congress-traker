import { clsx } from "clsx";
import type { ReactNode } from "react";

interface BadgeProps {
  children: ReactNode;
  className?: string;
  size?: "sm" | "md";
}

export function Badge({ children, className, size = "sm" }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded border font-medium",
        size === "sm" ? "px-1.5 py-0.5 text-xs" : "px-2 py-1 text-sm",
        className
      )}
    >
      {children}
    </span>
  );
}
