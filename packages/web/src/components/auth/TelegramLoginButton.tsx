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
    if (!botName) {
      console.warn("Telegram bot name not configured");
      return;
    }

    // Define the callback function
    const handleTelegramAuth = async (user: TelegramAuthData) => {
      try {
        // Call backend to verify and authenticate using auth context
        await telegramSignIn(user);

        // Navigate to dashboard
        navigate("/dashboard");
      } catch (error) {
        const errorMessage = handleApiError(error);
        if (onError) {
          onError(errorMessage);
        } else {
          console.error("Telegram authentication failed:", errorMessage);
        }
      }
    };

    // Make the callback globally accessible for Telegram widget
    window.TelegramLoginWidget = {
      dataOnauth: handleTelegramAuth,
    };

    // Load Telegram Widget script
    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.async = true;
    script.setAttribute("data-telegram-login", botName);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-radius", "8");
    script.setAttribute("data-onauth", "TelegramLoginWidget.dataOnauth(user)");
    script.setAttribute("data-request-access", "write");

    if (containerRef.current) {
      containerRef.current.appendChild(script);
    }

    return () => {
      // Cleanup
      if (containerRef.current && script.parentNode === containerRef.current) {
        containerRef.current.removeChild(script);
      }
      delete window.TelegramLoginWidget;
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
