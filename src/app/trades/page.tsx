import type { Metadata } from "next";
import { getTrades } from "@/lib/data/loader";
import { TradesClient } from "./TradesClient";

export const metadata: Metadata = {
  title: "All Trades",
  description: "Browse and filter all congressional stock trade disclosures.",
};

export const revalidate = parseInt(process.env.NEXT_REVALIDATE_SECONDS ?? "21600");

export default function TradesPage() {
  const trades = getTrades();

  return (
    <div className="space-y-4 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">All Trades</h1>
        <p className="mt-1 text-sm text-neutral-500">
          {trades.length.toLocaleString()} trade disclosures · Sorted by disclosure date
        </p>
      </div>
      <TradesClient trades={trades} />
    </div>
  );
}
