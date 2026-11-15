import api from './client';
import type { Manager } from '../types';

export const authApi = {
  register: async (data: { email: string; password: string; full_name: string }) => {
    const res = await api.post<Manager>('/api/auth/register', data);
    return res.data;
  },

  login: async (email: string, password: string): Promise<string> => {
    const res = await api.post<{ access_token: string; token_type: string }>(
      '/api/auth/login',
      { email, password }
    );
    return res.data.access_token;
  },

  me: async (): Promise<Manager> => {
    const res = await api.get<Manager>('/api/auth/me');
    return res.data;
  },
};
