"use client";

import { useState, type ReactNode } from "react";
import { clsx } from "clsx";

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  position?: "top" | "bottom" | "left" | "right";
  className?: string;
}

export function Tooltip({ content, children, position = "top", className }: TooltipProps) {
  const [visible, setVisible] = useState(false);

  const posClass = {
    top:    "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left:   "right-full top-1/2 -translate-y-1/2 mr-2",
    right:  "left-full top-1/2 -translate-y-1/2 ml-2",
  }[position];

  return (
    <div
      className={clsx("relative inline-block", className)}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div
          className={clsx(
            "absolute z-50 min-w-max max-w-xs rounded-md border border-surface-border bg-surface-raised px-3 py-2 text-xs text-neutral-300 shadow-xl",
            posClass
          )}
        >
          {content}
        </div>
      )}
    </div>
  );
}
