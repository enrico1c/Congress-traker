import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-surface-border bg-surface-muted py-8 mt-16">
      <div className="mx-auto max-w-screen-xl px-4">
        {/* Disclaimer */}
        <div className="mb-6 rounded-lg border border-yellow-500/20 bg-yellow-500/5 p-4">
          <p className="text-xs text-yellow-300/80 leading-relaxed">
            <strong className="text-yellow-300">Disclaimer:</strong>{" "}
            CongressTrades is a public-information transparency tool. It does not prove or imply
            wrongdoing. Trade disclosures are often delayed by up to 45 days and use value ranges,
            not exact figures. Portfolio performance estimates are reconstructed approximations
            — they are not audited and carry significant uncertainty. Policy overlap scores are
            informational signals, not legal conclusions. All data is sourced from public
            government filings under the STOCK Act.
          </p>
        </div>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-4 text-xs text-neutral-500">
            <Link href="/about" className="hover:text-white transition-colors">Methodology</Link>
            <Link href="/about#sources" className="hover:text-white transition-colors">Data Sources</Link>
            <Link href="/about#scoring" className="hover:text-white transition-colors">Scoring</Link>
            <a
              href="https://disclosures.house.gov"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white transition-colors"
            >
              House Disclosures ↗
            </a>
            <a
              href="https://efts.senate.gov"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white transition-colors"
            >
              Senate Disclosures ↗
            </a>
          </div>
          <p className="text-xs text-neutral-600">
            CongressTrades — public transparency tool · Not affiliated with any government entity
          </p>
        </div>
      </div>
    </footer>
  );
}
