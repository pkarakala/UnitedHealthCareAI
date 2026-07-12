import { PAClient } from "./client";

export const api = new PAClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});
