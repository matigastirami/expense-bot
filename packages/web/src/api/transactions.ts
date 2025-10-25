import { apiClient } from "./client";
import type { Transaction } from "../types";

export interface TransactionFilters {
  date_from: string;
  date_to: string;
  account_name?: string;
  transaction_type?: "income" | "expense" | "transfer" | "conversion";
  limit?: number;
  offset?: number;
}

export interface CreateTransactionRequest {
  transaction_type: "income" | "expense" | "transfer" | "conversion";
  amount: number;
  currency: string;
  date?: string;
  account_from?: string;
  account_to?: string;
  currency_to?: string;
  amount_to?: number;
  exchange_rate?: number;
  description?: string;
}

export interface UpdateTransactionRequest {
  amount?: number;
  description?: string;
  date?: string;
  type?: "income" | "expense" | "transfer" | "conversion";
  currency?: string;
  account_from?: string;
  account_to?: string;
  category_id?: number;
  merchant_id?: number;
  is_necessary?: boolean;
  currency_to?: string;
  amount_to?: number;
  exchange_rate?: number;
}

export const transactionsApi = {
  list: async (filters: TransactionFilters) => {
    const response = await apiClient.get<{
      transactions: Transaction[];
      count: number;
    }>("/transactions", {
      params: filters,
    });
    return response.data;
  },

  create: async (data: CreateTransactionRequest) => {
    const response = await apiClient.post<Transaction>("/transactions", data);
    return response.data;
  },

  update: async (id: number, data: UpdateTransactionRequest) => {
    const response = await apiClient.put<Transaction>(
      `/transactions/${id}`,
      data,
    );
    return response.data;
  },

  delete: async (id: number) => {
    const response = await apiClient.delete(`/transactions/${id}`);
    return response.data;
  },
};
