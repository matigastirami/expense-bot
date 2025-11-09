import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import type { TelegramAuthData } from "../../api/auth";
import { handleApiError } from "../../api/client";

interface TelegramLoginButtonProps {
  botName: string;
  onError?: (error: string) => void;
}

// Extend Window interface to include TelegramLoginWidget
declare global {
  interface Window {
    TelegramLoginWidget?: {
      dataOnauth?: (user: TelegramAuthData) => void;
    };
  }
}

export const TelegramLoginButton = ({
  botName,
  onError,
}: TelegramLoginButtonProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { telegramSignIn } = useAuth();

  useEffect(() => {
    console.log("TelegramLoginButton mounting, botName:", botName);
    console.log("Current window location:", window.location.href);

    if (!botName) {
      console.warn("Telegram bot name not configured");
      return;
    }

    // Check if we're coming back from Telegram with auth data
    const urlParams = new URLSearchParams(window.location.search);
    const telegramData: any = {};

    // Telegram sends these parameters: id, first_name, last_name, username, photo_url, auth_date, hash
    if (urlParams.has("id") && urlParams.has("hash")) {
      console.log("=== Telegram redirect detected ===");

      // Extract all Telegram parameters
      [
        "id",
        "first_name",
        "last_name",
        "username",
        "photo_url",
        "auth_date",
        "hash",
      ].forEach((key) => {
        const value = urlParams.get(key);
        if (value) {
          telegramData[key === "id" ? "id" : key] =
            key === "id" || key === "auth_date" ? parseInt(value) : value;
        }
      });

      console.log("Telegram auth data from URL:", telegramData);

      // Authenticate with backend
      const authenticate = async () => {
        try {
          console.log("Calling API to authenticate...");
          await telegramSignIn(telegramData as TelegramAuthData);

          console.log("Authentication successful, navigating to dashboard");
          // Clean URL and navigate to dashboard
          window.history.replaceState(
            {},
            document.title,
            window.location.pathname,
          );
          navigate("/dashboard");
        } catch (error) {
          const errorMessage = handleApiError(error);
          console.error("Telegram authentication failed:", errorMessage);
          console.error("Full error:", error);
          if (onError) {
            onError(errorMessage);
          }
        }
      };

      authenticate();
      return; // Don't load the widget if we're processing auth
    }

    // Load Telegram Widget script with redirect method
    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.async = true;
    script.setAttribute("data-telegram-login", botName);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-radius", "8");
    script.setAttribute("data-auth-url", window.location.href); // Use redirect instead of callback
    script.setAttribute("data-request-access", "write");

    script.onload = () => {
      console.log("Telegram widget script loaded successfully (redirect mode)");
    };

    script.onerror = (error) => {
      console.error("Failed to load Telegram widget script:", error);
    };

    console.log("Appending Telegram widget script to DOM (redirect mode)...");
    if (containerRef.current) {
      containerRef.current.appendChild(script);
    } else {
      console.error("Container ref is null, cannot append script");
    }

    return () => {
      // Cleanup
      if (containerRef.current && script.parentNode === containerRef.current) {
        containerRef.current.removeChild(script);
      }
    };
  }, [botName, navigate, onError, telegramSignIn]);

  if (!botName) {
    return (
      <div className="text-center text-sm text-gray-500 p-4 bg-gray-50 rounded-md">
        Telegram login not configured. Please set VITE_TELEGRAM_BOT_NAME
        environment variable.
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center">
      <div ref={containerRef} className="telegram-login-button" />
      <p className="text-xs text-gray-500 mt-2 text-center">
        Login securely with your Telegram account
      </p>
    </div>
  );
};
