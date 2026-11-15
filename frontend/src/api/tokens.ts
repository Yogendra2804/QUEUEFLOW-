import api from './client';
import type { Token } from '../types';

export const tokensApi = {
  list: async (queueId: number): Promise<Token[]> => {
    const res = await api.get<Token[]>(`/api/queues/${queueId}/tokens/`);
    return res.data;
  },

  register: async (queueId: number, person_name: string, person_phone: string): Promise<Token> => {
    const res = await api.post<Token>(`/api/queues/${queueId}/tokens/`, {
      person_name,
      person_phone,
    });
    return res.data;
  },

  callNext: async (queueId: number): Promise<Token> => {
    const res = await api.post<Token>(`/api/queues/${queueId}/tokens/call-next`);
    return res.data;
  },

  complete: async (queueId: number, tokenId: number): Promise<Token> => {
    const res = await api.post<Token>(`/api/queues/${queueId}/tokens/${tokenId}/complete`);
    return res.data;
  },

  cancel: async (queueId: number, tokenId: number): Promise<Token> => {
    const res = await api.post<Token>(`/api/queues/${queueId}/tokens/${tokenId}/cancel`);
    return res.data;
  },

  moveUp: async (queueId: number, tokenId: number): Promise<Token[]> => {
    const res = await api.post<Token[]>(`/api/queues/${queueId}/tokens/${tokenId}/move-up`);
    return res.data;
  },

  moveDown: async (queueId: number, tokenId: number): Promise<Token[]> => {
    const res = await api.post<Token[]>(`/api/queues/${queueId}/tokens/${tokenId}/move-down`);
    return res.data;
  },
};
