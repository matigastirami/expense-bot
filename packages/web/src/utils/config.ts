export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
export const TELEGRAM_BOT_NAME = import.meta.env.VITE_TELEGRAM_BOT_NAME || "";

// Log configuration for debugging
if (import.meta.env.DEV) {
  console.log("Config:", {
    API_BASE_URL,
    TELEGRAM_BOT_NAME: TELEGRAM_BOT_NAME || "(not configured)",
  });
}
