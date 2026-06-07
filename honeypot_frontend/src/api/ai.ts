import apiClient from './client';
import type {
  AIAnalysisRequest,
  AIAnalysisResponse,
  InvestigationRequest,
  InvestigationResponse,
  SimilarAttackSummary,
} from '../types';

export const aiApi = {
  analyze: async (
    request: AIAnalysisRequest
  ): Promise<AIAnalysisResponse> => {
    const { data } = await apiClient.post<AIAnalysisResponse>(
      '/ai/analyze',
      request
    );
    return data;
  },
  investigate: async (
    request: InvestigationRequest
  ): Promise<InvestigationResponse> => {
    const { data } = await apiClient.post<InvestigationResponse>(
      '/ai/investigate',
      request
    );
    return data;
  },
  getSimilarAttacks: async (
    attackId: string
  ): Promise<SimilarAttackSummary[]> => {
    const { data } = await apiClient.get<SimilarAttackSummary[]>(
      `/ai/similar/${attackId}`
    );
    return data;
  },
};
