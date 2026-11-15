import api from './client';
import type { Queue } from '../types';

export const queuesApi = {
  list: async (): Promise<Queue[]> => {
    const res = await api.get<Queue[]>('/api/queues/');
    return res.data;
  },

  create: async (name: string, description: string): Promise<Queue> => {
    const res = await api.post<Queue>('/api/queues/', { name, description });
    return res.data;
  },

  get: async (id: number): Promise<Queue> => {
    const res = await api.get<Queue>(`/api/queues/${id}`);
    return res.data;
  },

  update: async (id: number, name: string, description: string): Promise<Queue> => {
    const res = await api.put<Queue>(`/api/queues/${id}`, { name, description });
    return res.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/queues/${id}`);
  },
};
