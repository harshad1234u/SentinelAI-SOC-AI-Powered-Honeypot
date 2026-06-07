import apiClient from './client';
import type {
  AttackListResponse,
  TopAttacker,
  CountryStats,
  TimelineBucket,
} from '../types';

export interface AttackQueryParams {
  service?: string;
  severity?: string;
  src_ip?: string;
  country?: string;
  reputation?: string;
  page?: number;
  page_size?: number;
}

export const attacksApi = {
  getLiveAttacks: async (
    params: AttackQueryParams = {}
  ): Promise<AttackListResponse> => {
    const { data } = await apiClient.get<AttackListResponse>('/attacks/live', {
      params,
    });
    return data;
  },
  getTopAttackers: async (limit = 10): Promise<TopAttacker[]> => {
    const { data } = await apiClient.get<TopAttacker[]>('/top-attackers', {
      params: { limit },
    });
    return data;
  },
  getCountries: async (): Promise<CountryStats[]> => {
    const { data } = await apiClient.get<CountryStats[]>('/countries');
    return data;
  },
  getTimeline: async (interval = '1h'): Promise<TimelineBucket[]> => {
    const { data } = await apiClient.get<TimelineBucket[]>('/timeline', {
      params: { interval },
    });
    return data;
  },
};
