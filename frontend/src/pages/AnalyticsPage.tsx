import { useState, useEffect, useCallback } from 'react';
import { analyticsApi } from '../api/analytics';
import type { OverallAnalytics, QueueAnalytics } from '../types';
import { Navbar } from '../components/Navbar';
import { Spinner } from '../components/ui/Spinner';
import { EmptyState } from '../components/ui/EmptyState';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import { BarChart2, Users, CheckCircle2, XCircle, Clock } from 'lucide-react';
import toast from 'react-hot-toast';

function StatCard({
  label,
  value,
  icon,
  color = 'blue',
  unit,
}: {
  label: string;
  value: number | string | null;
  icon: React.ReactNode;
  color?: 'blue' | 'green' | 'red' | 'yellow';
  unit?: string;
}) {
  const colorMap = {
    blue: 'text-blue-600 bg-blue-50',
    green: 'text-green-600 bg-green-50',
    red: 'text-red-600 bg-red-50',
    yellow: 'text-yellow-600 bg-yellow-50',
  };
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {value === null ? '—' : value}
            {unit && value !== null && (
              <span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>
            )}
          </p>
        </div>
        <div className={`p-2 rounded-lg ${colorMap[color]}`}>{icon}</div>
      </div>
    </div>
  );
}

function QueueAnalyticsCard({ qa }: { qa: QueueAnalytics }) {
  return (
    <div className="card">
      <h3 className="font-semibold text-gray-900 mb-1">{qa.queue_name}</h3>
      <div className="grid grid-cols-3 gap-2 text-sm mb-4">
        <div className="text-center">
          <p className="font-bold text-gray-900">{qa.total_tokens}</p>
          <p className="text-gray-500 text-xs">Total</p>
        </div>
        <div className="text-center">
          <p className="font-bold text-green-700">{qa.completed_tokens}</p>
          <p className="text-gray-500 text-xs">Completed</p>
        </div>
        <div className="text-center">
          <p className="font-bold text-red-600">{qa.cancelled_tokens}</p>
          <p className="text-gray-500 text-xs">Cancelled</p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm mb-4">
        <div>
          <p className="text-gray-500 text-xs">Avg wait</p>
          <p className="font-medium">
            {qa.avg_wait_minutes !== null ? `${qa.avg_wait_minutes} min` : '—'}
          </p>
        </div>
        <div>
          <p className="text-gray-500 text-xs">Avg service</p>
          <p className="font-medium">
            {qa.avg_service_minutes !== null ? `${qa.avg_service_minutes} min` : '—'}
          </p>
        </div>
      </div>
      {/* 7-day chart */}
      <div className="mt-4">
        <p className="text-xs text-gray-500 mb-2">Last 7 days</p>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={qa.daily_stats} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tickFormatter={(d: string) => new Date(d).toLocaleDateString('en', { weekday: 'short' })}
              tick={{ fontSize: 10 }}
            />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip
              labelFormatter={(label: any) => (label ? new Date(label).toLocaleDateString() : '')}
            />
            <Bar dataKey="completed" fill="#22c55e" name="Completed" radius={[2, 2, 0, 0]} />
            <Bar dataKey="cancelled" fill="#ef4444" name="Cancelled" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function AnalyticsPage() {
  const [data, setData] = useState<OverallAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = useCallback(async () => {
    try {
      const d = await analyticsApi.get();
      setData(d);
    } catch {
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
    const id = setInterval(fetchAnalytics, 30_000);
    return () => clearInterval(id);
  }, [fetchAnalytics]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-500 text-sm mt-1">Real-time statistics across all your queues</p>
        </div>

        {loading && (
          <div className="flex justify-center py-16">
            <Spinner size="lg" />
          </div>
        )}

        {!loading && data && (
          <>
            {/* overall stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard
                label="Total Queues"
                value={data.total_queues}
                icon={<BarChart2 size={20} />}
                color="blue"
              />
              <StatCard
                label="Tokens Today"
                value={data.total_tokens_today}
                icon={<Users size={20} />}
                color="yellow"
              />
              <StatCard
                label="Completed Today"
                value={data.total_completed_today}
                icon={<CheckCircle2 size={20} />}
                color="green"
              />
              <StatCard
                label="Cancelled Today"
                value={data.total_cancelled_today}
                icon={<XCircle size={20} />}
                color="red"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              <StatCard
                label="Avg Wait Time"
                value={data.avg_wait_minutes}
                icon={<Clock size={20} />}
                color="blue"
                unit="min"
              />
              <StatCard
                label="Avg Service Duration"
                value={data.avg_service_minutes}
                icon={<Clock size={20} />}
                color="green"
                unit="min"
              />
            </div>

            {/* per-queue analytics */}
            {data.queue_analytics.length === 0 ? (
              <EmptyState
                icon={<BarChart2 size={48} />}
                title="No queue data yet"
                description="Create a queue and start processing tokens to see analytics."
              />
            ) : (
              <>
                <h2 className="text-lg font-semibold text-gray-800 mb-4">Per-Queue Breakdown</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {data.queue_analytics.map((qa) => (
                    <QueueAnalyticsCard key={qa.queue_id} qa={qa} />
                  ))}
                </div>
              </>
            )}

            {/* combined daily trend */}
            {data.queue_analytics.length > 0 && (() => {
              // aggregate daily stats across all queues
              const dayMap: Record<string, { date: string; total: number; completed: number }> = {};
              data.queue_analytics.forEach((qa) => {
                qa.daily_stats.forEach((d) => {
                  if (!dayMap[d.date]) dayMap[d.date] = { date: d.date, total: 0, completed: 0 };
                  dayMap[d.date].total += d.total;
                  dayMap[d.date].completed += d.completed;
                });
              });
              const combined = Object.values(dayMap).sort((a, b) => a.date.localeCompare(b.date));
              return (
                <div className="card mt-6">
                  <h2 className="font-semibold text-gray-800 mb-4">7-Day Overall Trend</h2>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={combined} margin={{ top: 0, right: 20, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis
                        dataKey="date"
                        tickFormatter={(d: string) => new Date(d).toLocaleDateString('en', { weekday: 'short' })}
                        tick={{ fontSize: 11 }}
                      />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip labelFormatter={(label: any) => (label ? new Date(label).toLocaleDateString() : '')} />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="total"
                        name="Total Tokens"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="completed"
                        name="Completed"
                        stroke="#22c55e"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              );
            })()}
          </>
        )}
      </main>
    </div>
  );
}
