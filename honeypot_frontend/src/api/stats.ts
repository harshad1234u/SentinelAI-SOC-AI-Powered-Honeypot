import apiClient from './client';
import type { DashboardStats } from '../types';

export const statsApi = {
  getDashboardStats: async (): Promise<DashboardStats> => {
    const { data } = await apiClient.get<DashboardStats>('/stats');
    return data;
  },
};
