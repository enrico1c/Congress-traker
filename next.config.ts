import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Output static pages where possible; API routes remain serverless
  output: "standalone",

  // Allow images from external sources used in member photos
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "theunitedstates.io",
      },
      {
        protocol: "https",
        hostname: "www.congress.gov",
      },
    ],
    unoptimized: true, // Simplify for Vercel free tier
  },

  // Webpack: allow reading JSON data artifacts from /data directory
  webpack(config) {
    config.resolve.alias = {
      ...config.resolve.alias,
    };
    return config;
  },

  // Headers for caching static data artifacts
  async headers() {
    return [
      {
        source: "/api/:path*",
        headers: [
          { key: "Cache-Control", value: "s-maxage=3600, stale-while-revalidate=86400" },
        ],
      },
    ];
  },
};

export default nextConfig;
