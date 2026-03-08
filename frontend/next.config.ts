import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },

  // ── Image optimization ──────────────────────────────────────
  images: {
    remotePatterns: [
      // Cloudflare R2 public storage
      {
        protocol: "https",
        hostname: "pub-b8827eb1b55d4da88d00d158e2f0d22b.r2.dev",
        pathname: "/**",
      },
      // Unsplash (used in homepage & archive)
      {
        protocol: "https",
        hostname: "images.unsplash.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "plus.unsplash.com",
        pathname: "/**",
      },
      // Production CDN / custom image host (adjust if needed)
      {
        protocol: "https",
        hostname: "moku.com",
      },
    ],
  },

  // ── API rewrites (proxy to backend in production) ───────────
  // This allows the frontend to call /api/* without CORS issues
  // when deployed on Vercel, and avoids exposing the backend URL.
  async rewrites() {
    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },

  // ── Security headers ────────────────────────────────────────
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
