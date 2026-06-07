import apiClient from './client';
import type { AlertResponse } from '../types';

export const alertsApi = {
  getHistory: async (): Promise<AlertResponse[]> => {
    const { data } = await apiClient.get<AlertResponse[]>('/alerts/history');
    return data;
  },
  testAlert: async (
    message?: string
  ): Promise<{ success: boolean }> => {
    const { data } = await apiClient.post<{ success: boolean }>(
      '/alerts/test',
      { message }
    );
    return data;
  },
};
