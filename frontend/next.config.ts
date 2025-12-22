import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  allowedDevOrigins: ["http://localhost:3000",
    "http://localhost:8000",
    "unelectrical-toi-nonviolably.ngrok-free.dev"],
};

export default nextConfig;
