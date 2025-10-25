import { apiClient } from "./client";
import type { Analytics } from "../types";

export interface AnalyticsFilters {
  date_from: string;
  date_to: string;
  currency?: string;
}

export const analyticsApi = {
  getAnalytics: async (filters: AnalyticsFilters) => {
    const response = await apiClient.get<Analytics>("/analytics", {
      params: filters,
    });
    return response.data;
  },
};
