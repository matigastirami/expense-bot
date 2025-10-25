import { apiClient } from "./client";
import type { Account } from "../types";

export interface CreateAccountRequest {
  name: string;
  type: "bank" | "wallet" | "cash" | "other";
  track_balance?: boolean;
}

export interface UpdateAccountRequest {
  name?: string;
  type?: "bank" | "wallet" | "cash" | "other";
  track_balance?: boolean;
}

export const accountsApi = {
  list: async (includeBalances = true) => {
    const response = await apiClient.get<{
      accounts: Account[];
      count: number;
    }>("/accounts", {
      params: { include_balances: includeBalances },
    });
    return response.data;
  },

  create: async (data: CreateAccountRequest) => {
    const response = await apiClient.post<Account>("/accounts", data);
    return response.data;
  },

  update: async (id: number, data: UpdateAccountRequest) => {
    const response = await apiClient.put<Account>(`/accounts/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    const response = await apiClient.delete(`/accounts/${id}`);
    return response.data;
  },

  getBalances: async (accountName?: string) => {
    const response = await apiClient.get("/accounts/balances", {
      params: accountName ? { account_name: accountName } : {},
    });
    return response.data;
  },
};
