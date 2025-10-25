import { apiClient } from "./client";
import type { Category } from "../types";

export interface CreateCategoryRequest {
  name: string;
  type: "income" | "expense";
}

export interface UpdateCategoryRequest {
  name?: string;
  type?: "income" | "expense";
}

export const categoriesApi = {
  list: async () => {
    const response = await apiClient.get<{ categories: Category[] }>(
      "/categories",
    );
    return response.data;
  },

  create: async (data: CreateCategoryRequest) => {
    const response = await apiClient.post<Category>("/categories", data);
    return response.data;
  },

  update: async (id: number, data: UpdateCategoryRequest) => {
    const response = await apiClient.put<Category>(`/categories/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    const response = await apiClient.delete(`/categories/${id}`);
    return response.data;
  },
};
