import { apiClient } from "./client";
import type { AuthResponse } from "../types";

export interface SignInRequest {
  email: string;
  password: string;
}

export interface SignUpRequest {
  email: string;
  password: string;
  language_code?: string;
}

export interface LinkTelegramRequest {
  telegram_user_id: string;
}

export interface TelegramAuthData {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
}

export interface TelegramAuthResponse extends AuthResponse {
  is_new_user: boolean;
}

export const authApi = {
  signIn: async (data: SignInRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/signin", data);
    return response.data;
  },

  signUp: async (data: SignUpRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/signup", data);
    return response.data;
  },

  telegramAuth: async (
    data: TelegramAuthData,
  ): Promise<TelegramAuthResponse> => {
    const response = await apiClient.post<TelegramAuthResponse>(
      "/auth/telegram",
      data,
    );
    return response.data;
  },

  linkTelegram: async (
    data: LinkTelegramRequest,
  ): Promise<{ message: string }> => {
    const response = await apiClient.post("/link-telegram", data);
    return response.data;
  },
};
