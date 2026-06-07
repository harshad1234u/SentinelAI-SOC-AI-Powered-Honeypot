import apiClient from './client';
import type { TokenResponse, UserResponse } from '../types';

export const authApi = {
  login: async (
    username: string,
    password: string
  ): Promise<TokenResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const { data } = await apiClient.post<TokenResponse>(
      '/auth/login',
      formData,
      {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      }
    );
    return data;
  },
  refresh: async (): Promise<TokenResponse> => {
    const { data } = await apiClient.post<TokenResponse>('/auth/refresh');
    return data;
  },
  me: async (): Promise<UserResponse> => {
    const { data } = await apiClient.get<UserResponse>('/auth/me');
    return data;
  },
};
