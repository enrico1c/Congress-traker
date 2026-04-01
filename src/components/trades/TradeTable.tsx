"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  type ColumnDef,
  type SortingState,
  flexRender,
} from "@tanstack/react-table";
import { ChevronUp, ChevronDown, ChevronsUpDown, ExternalLink, ChevronLeft, ChevronRight } from "lucide-react";
import { clsx } from "clsx";
import { Badge } from "@/components/ui/Badge";
import { FlagBadge } from "@/components/trades/FlagBadge";
import {
  formatDate,
  formatAmountRange,
  partyBgClass,
  partyShort,
  tradeTypeBgClass,
} from "@/lib/utils/formatting";
import type { Trade } from "@/lib/types";

interface TradeTableProps {
  trades: Trade[];
  showMember?: boolean;
  showCompany?: boolean;
  pageSize?: number;
}

export function TradeTable({
  trades,
  showMember = true,
  showCompany = true,
  pageSize = 25,
}: TradeTableProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: "disclosureDate", desc: true },
  ]);

  const columns = useMemo<ColumnDef<Trade>[]>(() => {
    const cols: ColumnDef<Trade>[] = [];

    if (showMember) {
      cols.push({
        id: "member",
        header: "Member",
        accessorFn: (r) => r.memberName,
        cell: ({ row }) => {
          const t = row.original;
          return (
            <div className="flex items-center gap-2">
              <Badge className={partyBgClass(t.memberParty)}>
                {partyShort(t.memberParty)}
              </Badge>
              <div>
                <Link
                  href={`/members/${t.memberSlug}`}
                  className="text-sm font-medium text-white hover:text-brand-400 transition-colors"
                >
                  {t.memberName}
                </Link>
                <p className="text-xs text-neutral-500">{t.memberState} · {t.memberChamber}</p>
              </div>
            </div>
          );
        },
      });
    }

    if (showCompany) {
      cols.push({
        id: "company",
        header: "Company",
        accessorFn: (r) => r.companyName,
        cell: ({ row }) => {
          const t = row.original;
          return (
            <div>
              <Link
                href={`/companies/${t.ticker}`}
                className="text-sm font-medium text-white hover:text-brand-400 transition-colors"
              >
                {t.ticker}
              </Link>
              <p className="text-xs text-neutral-500 truncate max-w-36">{t.companyName}</p>
            </div>
          );
        },
      });
    }

    cols.push(
      {
        id: "tradeType",
        header: "Type",
        accessorFn: (r) => r.tradeType,
        cell: ({ getValue }) => (
          <Badge className={tradeTypeBgClass(getValue<string>())}>
            {getValue<string>().replace(" (Partial)", "*")}
          </Badge>
        ),
      },
      {
        id: "amount",
        header: "Amount",
        accessorFn: (r) => r.amount.min,
        cell: ({ row }) => (
          <span className="text-xs text-neutral-300 whitespace-nowrap">
            {formatAmountRange(row.original.amount)}
          </span>
        ),
      },
      {
        id: "tradeDate",
        header: "Trade Date",
        accessorFn: (r) => r.tradeDate,
        cell: ({ getValue }) => (
          <span className="text-xs text-neutral-400 whitespace-nowrap">
            {formatDate(getValue<string>())}
          </span>
        ),
      },
      {
        id: "disclosureDate",
        header: "Disclosed",
        accessorFn: (r) => r.disclosureDate,
        cell: ({ row }) => {
          const t = row.original;
          return (
            <div>
              <span className="text-xs text-neutral-400 whitespace-nowrap">
                {formatDate(t.disclosureDate)}
              </span>
              {t.disclosureDelay > 45 && (
                <p className="text-xs text-orange-400">+{t.disclosureDelay}d late</p>
              )}
            </div>
          );
        },
      },
      {
        id: "flag",
        header: "Overlap",
        accessorFn: (r) => r.flagScore ?? 0,
        cell: ({ row }) => {
          const t = row.original;
          if (!t.isFlagged) return <span className="text-xs text-neutral-600">—</span>;
          return (
            <FlagBadge
              severity={t.flagSeverity!}
              score={t.flagScore!}
              tradeId={t.id}
            />
          );
        },
      },
      {
        id: "source",
        header: "",
        enableSorting: false,
        cell: ({ row }) => (
          <a
            href={row.original.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-neutral-500 hover:text-white transition-colors"
            title="View original disclosure"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        ),
      }
    );

    return cols;
  }, [showMember, showCompany]);

  const table = useReactTable({
    data: trades,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize } },
  });

  return (
    <div className="w-full">
      <div className="overflow-x-auto rounded-lg border border-surface-border">
        <table className="w-full text-left">
          <thead className="border-b border-surface-border bg-surface-muted">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-neutral-500"
                  >
                    {header.isPlaceholder ? null : (
                      <div
                        className={clsx(
                          "flex items-center gap-1",
                          header.column.getCanSort() && "cursor-pointer select-none hover:text-white"
                        )}
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {header.column.getCanSort() && (
                          <span className="text-neutral-600">
                            {header.column.getIsSorted() === "asc"  ? <ChevronUp className="h-3 w-3" /> :
                             header.column.getIsSorted() === "desc" ? <ChevronDown className="h-3 w-3" /> :
                             <ChevronsUpDown className="h-3 w-3" />}
                          </span>
                        )}
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row, i) => (
              <tr
                key={row.id}
                className={clsx(
                  "border-b border-surface-border/50 transition-colors hover:bg-surface-raised/50",
                  i % 2 === 0 ? "bg-transparent" : "bg-surface-muted/30",
                  row.original.isFlagged && "border-l-2 border-l-red-500/50"
                )}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2.5">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
            {table.getRowModel().rows.length === 0 && (
              <tr>
                <td
                  colSpan={columns.length}
                  className="py-12 text-center text-sm text-neutral-500"
                >
                  No trades found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {table.getPageCount() > 1 && (
        <div className="mt-3 flex items-center justify-between text-xs text-neutral-500">
          <p>
            {table.getState().pagination.pageIndex * pageSize + 1}–
            {Math.min((table.getState().pagination.pageIndex + 1) * pageSize, trades.length)} of{" "}
            {trades.length} trades
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="rounded p-1 hover:bg-surface-raised disabled:opacity-30"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span>
              Page {table.getState().pagination.pageIndex + 1} / {table.getPageCount()}
            </span>
            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="rounded p-1 hover:bg-surface-raised disabled:opacity-30"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
