import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Всё, что идёт на /api, проксируется на FastAPI backend (см. backend/app/main.py)
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
      "/snapshots": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/photos": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
