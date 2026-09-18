import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // GitHub Pages only serves static files — no Node server for SSR,
  // route handlers, or next/image's default optimizer.
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
