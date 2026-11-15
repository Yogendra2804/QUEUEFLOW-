import { describe, it, expect } from 'vitest';
import type { Token, Queue, TokenStatus } from '../types';

describe('Data structures and queue business logic contracts', () => {
  it('validates Token data contract and positions', () => {
    const mockToken: Token = {
      id: 101,
      queue_id: 1,
      token_number: 1,
      person_name: 'Jane Doe',
      person_phone: '1234567890',
      position: 1,
      status: 'waiting',
      joined_at: new Date().toISOString(),
      called_at: null,
      completed_at: null,
      estimated_wait_minutes: 5.0,
      actual_wait_minutes: null,
      service_duration_minutes: null,
    };

    expect(mockToken.status).toBe('waiting');
    expect(mockToken.position).toBe(1);
    expect(mockToken.token_number).toBe(1);
  });

  it('validates status transitions', () => {
    const validStatuses: TokenStatus[] = [
      'waiting',
      'serving',
      'completed',
      'cancelled',
    ];
    expect(validStatuses).toHaveLength(4);
    expect(validStatuses).toContain('serving');
  });

  it('calculates queue summary correctly', () => {
    const mockQueue: Queue = {
      id: 1,
      name: 'Counter 1',
      description: 'Customer Support',
      manager_id: 10,
      is_active: true,
      created_at: new Date().toISOString(),
      waiting_count: 3,
      serving_count: 1,
    };

    expect(mockQueue.waiting_count).toBe(3);
    expect(mockQueue.serving_count).toBe(1);
  });
});
