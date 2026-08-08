import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 프론트는 상대경로 /api 로 호출 → 개발 중엔 백엔드로 프록시, 배포 시 CloudFront가 /api/* 를 EC2로 라우팅
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
