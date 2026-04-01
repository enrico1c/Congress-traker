"use client";

import { Search, X } from "lucide-react";
import { clsx } from "clsx";

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export function SearchInput({
  value,
  onChange,
  placeholder = "Search…",
  className,
}: SearchInputProps) {
  return (
    <div className={clsx("relative", className)}>
      <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-neutral-500" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-md border border-surface-border bg-surface-muted py-2 pl-9 pr-8 text-sm text-white placeholder-neutral-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
      />
      {value && (
        <button
          onClick={() => onChange("")}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-neutral-500 hover:text-white"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}
