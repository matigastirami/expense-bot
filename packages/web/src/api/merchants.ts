import { apiClient } from "./client";
import type { Merchant } from "../types";

export interface CreateMerchantRequest {
  name: string;
}

export interface UpdateMerchantRequest {
  name?: string;
}

export const merchantsApi = {
  list: async () => {
    const response = await apiClient.get<{ merchants: Merchant[] }>(
      "/merchants",
    );
    return response.data;
  },

  create: async (data: CreateMerchantRequest) => {
    const response = await apiClient.post<Merchant>("/merchants", data);
    return response.data;
  },

  update: async (id: number, data: UpdateMerchantRequest) => {
    const response = await apiClient.put<Merchant>(`/merchants/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    const response = await apiClient.delete(`/merchants/${id}`);
    return response.data;
  },
};
