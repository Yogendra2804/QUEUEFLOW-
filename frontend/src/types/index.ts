// All shared TypeScript types

export interface Manager {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface Queue {
  id: number;
  name: string;
  description: string;
  manager_id: number;
  is_active: boolean;
  created_at: string;
  waiting_count: number;
  serving_count: number;
}

export type TokenStatus = 'waiting' | 'serving' | 'completed' | 'cancelled';

export interface Token {
  id: number;
  queue_id: number;
  token_number: number;
  person_name: string;
  person_phone: string;
  position: number | null;
  status: TokenStatus;
  joined_at: string;
  called_at: string | null;
  completed_at: string | null;
  estimated_wait_minutes: number | null;
  actual_wait_minutes: number | null;
  service_duration_minutes: number | null;
}

export interface DailyStat {
  date: string;
  total: number;
  completed: number;
  cancelled: number;
}

export interface QueueAnalytics {
  queue_id: number;
  queue_name: string;
  total_tokens: number;
  completed_tokens: number;
  cancelled_tokens: number;
  waiting_tokens: number;
  serving_tokens: number;
  avg_wait_minutes: number | null;
  avg_service_minutes: number | null;
  daily_stats: DailyStat[];
}

export interface OverallAnalytics {
  total_queues: number;
  total_tokens_today: number;
  total_completed_today: number;
  total_cancelled_today: number;
  avg_wait_minutes: number | null;
  avg_service_minutes: number | null;
  queue_analytics: QueueAnalytics[];
}
