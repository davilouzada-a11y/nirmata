import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        critical: "#e5484d",
        warn: "#ffb454",
      },
    },
  },
  plugins: [],
};

export default config;
