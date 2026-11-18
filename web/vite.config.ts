/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Relative base so the built site works from any folder (or file server).
export default defineConfig({
  base: "./",
  plugins: [react()],
  // Pre-bundle up front so a mid-session re-optimisation can't load two copies of React.
  optimizeDeps: { include: ["react", "react-dom", "react-dom/client", "react/jsx-runtime", "motion/react"] },
  test: {
    include: ["src/**/*.test.ts"],
  },
});
