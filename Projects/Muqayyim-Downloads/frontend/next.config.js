/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
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
