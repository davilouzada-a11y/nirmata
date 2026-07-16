import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      dwv: path.join(__dirname, "node_modules/dwv/dist/dwv.min.js"),
    };
    return config;
  },
};

export default nextConfig;
