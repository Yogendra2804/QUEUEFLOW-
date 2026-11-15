import api from './client';
import type { OverallAnalytics } from '../types';

export const analyticsApi = {
  get: async (): Promise<OverallAnalytics> => {
    const res = await api.get<OverallAnalytics>('/api/analytics/');
    return res.data;
  },
};
