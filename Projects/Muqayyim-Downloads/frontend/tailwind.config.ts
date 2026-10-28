import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#EFF6FF",
          100: "#DBEAFE",
          500: "#1F4E79",
          600: "#1A4068",
          700: "#153357",
          900: "#0B1D33",
        },
      },
    },
  },
  plugins: [],
};
export default config;
