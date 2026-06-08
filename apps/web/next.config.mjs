import path from "node:path";

const standaloneOutput = process.env.RANKKIT_STANDALONE === "true";

/** @type {import("next").NextConfig} */
const nextConfig = {
  ...(standaloneOutput ? { output: "standalone" } : {}),
  experimental: {
    outputFileTracingRoot: path.join(process.cwd(), "../.."),
  },
};

export default nextConfig;
