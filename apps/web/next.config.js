const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  compress: true, // Enable gzip compression
  poweredByHeader: false, // Remove X-Powered-By header for security/bytes

  transpilePackages: [
    "@neuraxis/ui",
    "@neuraxis/shared-types",
    "@neuraxis/utils",
  ],

  images: {
    formats: ["image/avif", "image/webp"], // Modern formats
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.neuraxis.ai",
      },
    ],
  },

  compiler: {
    // Remove console.log in production
    removeConsole:
      process.env.NODE_ENV === "production"
        ? {
            exclude: ["error", "warn"],
          }
        : false,
  },

  experimental: {
    optimizePackageImports: ["lucide-react", "recharts", "@mantine/core"], // Tree shaping
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          // Caching for static assets (Next.js handles mostly, but extra safety)
          {
            key: "Cache-Control",
            value: "public, max-age=3600, must-revalidate", // 1 hour default for pages
          },
        ],
      },
      {
        // Aggressive caching for immutable assets
        source: "/_next/static/(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
    ];
  },

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/v1/:path*", // Proxy to Backend
      },
    ];
  },
};

module.exports = withBundleAnalyzer(nextConfig);
