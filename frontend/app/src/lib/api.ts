import { PAClient } from "./client";
import { clearToken, getToken } from "./auth";

export const api = new PAClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  getToken,
  onUnauthorized: () => {
    clearToken();
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  },
});
