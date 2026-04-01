import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";

export const metadata: Metadata = {
  title: {
    default: "CongressTrades — Congressional Stock Trade Tracker",
    template: "%s | CongressTrades",
  },
  description:
    "Track U.S. congressional stock trades, detect policy-area overlaps, and explore reconstructed portfolio performance. Based on public STOCK Act disclosures.",
  keywords: [
    "congress stock trades",
    "STOCK Act",
    "congressional trading",
    "insider trading congress",
    "policy overlap",
    "congressional disclosures",
  ],
  openGraph: {
    title: "CongressTrades",
    description: "Congressional stock trade transparency platform",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-surface min-h-screen text-white antialiased">
        <Header />
        <main className="mx-auto max-w-screen-xl px-4 py-6">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
