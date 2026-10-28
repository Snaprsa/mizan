/** @type {import('next').NextConfig} */
const nextConfig = {
  // A dev/test server must not share the production build output used by `next start`.
  distDir: process.env.MIZAN_NEXT_DIST_DIR || ".next",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        // MIZAN_API_ORIGIN lets a dev/test frontend target a disposable API; default is the local API.
        destination: `${process.env.MIZAN_API_ORIGIN || "http://127.0.0.1:8000"}/api/:path*`,
      },
    ];
  },
  webpack: (config, { dev }) => {
    if (dev) {
      // Disable webpack cache to avoid permission issues on mounted FS
      config.cache = false;
    }
    return config;
  },
};
module.exports = nextConfig;
