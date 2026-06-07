import apiClient from './client';
import type { AttackListResponse } from '../types';

export const searchApi = {
  search: async (
    q: string,
    fields?: string,
    page = 1,
    pageSize = 50
  ): Promise<AttackListResponse> => {
    const { data } = await apiClient.get<AttackListResponse>('/search/', {
      params: { q, fields, page, page_size: pageSize },
    });
    return data;
  },
  semanticSearch: async (
    q: string,
    page = 1,
    pageSize = 50
  ): Promise<AttackListResponse> => {
    const { data } = await apiClient.get<AttackListResponse>(
      '/search/semantic',
      {
        params: { q, page, page_size: pageSize },
      }
    );
    return data;
  },
};
