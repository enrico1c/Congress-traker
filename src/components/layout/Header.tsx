"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { BarChart2, Users, Building2, AlertTriangle, TrendingUp, BookOpen, Activity } from "lucide-react";

const NAV = [
  { href: "/",           label: "Dashboard",  icon: Activity },
  { href: "/trades",     label: "All Trades", icon: BarChart2 },
  { href: "/flags",      label: "Flagged",    icon: AlertTriangle },
  { href: "/members",    label: "Members",    icon: Users },
  { href: "/companies",  label: "Companies",  icon: Building2 },
  { href: "/performers", label: "Performers", icon: TrendingUp },
  { href: "/about",      label: "Methodology",icon: BookOpen },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-surface-border bg-surface/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-screen-xl items-center justify-between px-4">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 font-bold text-white hover:text-brand-500 transition-colors"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-600 text-xs font-black text-white">
            CT
          </span>
          <span className="hidden sm:block">CongressTrades</span>
        </Link>

        {/* Nav */}
        <nav className="flex items-center gap-1 overflow-x-auto scrollbar-hide">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || (href !== "/" && pathname.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors whitespace-nowrap",
                  active
                    ? "bg-brand-600/20 text-brand-400"
                    : "text-neutral-400 hover:bg-surface-raised hover:text-white"
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                <span className="hidden md:block">{label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
