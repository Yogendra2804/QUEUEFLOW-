import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { queuesApi } from '../api/queues';
import { tokensApi } from '../api/tokens';
import type { Queue, Token } from '../types';
import { Navbar } from '../components/Navbar';
import { Spinner } from '../components/ui/Spinner';
import { EmptyState } from '../components/ui/EmptyState';
import toast from 'react-hot-toast';
import {
  ArrowLeft,
  ArrowUp,
  ArrowDown,
  UserPlus,
  PhoneCall,
  CheckCircle2,
  XCircle,
  Clock,
  Users,
  Zap,
} from 'lucide-react';
import { clsx } from 'clsx';

function TokenCard({
  token,
  queueId,
  onRefresh,
  isFirst,
  isLast,
}: {
  token: Token;
  queueId: number;
  onRefresh: () => void;
  isFirst: boolean;
  isLast: boolean;
}) {
  const [busy, setBusy] = useState(false);

  const act = async (fn: () => Promise<unknown>, msg: string) => {
    setBusy(true);
    try {
      await fn();
      toast.success(msg);
      onRefresh();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || 'Action failed');
    } finally {
      setBusy(false);
    }
  };

  const isServing = token.status === 'serving';
  const isWaiting = token.status === 'waiting';

  return (
    <div
      className={clsx(
        'rounded-xl border p-4 transition-all',
        isServing
          ? 'border-green-300 bg-green-50 shadow-md'
          : 'border-gray-200 bg-white hover:border-gray-300'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        {/* position badge + info */}
        <div className="flex items-start gap-3">
          <div
            className={clsx(
              'flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center font-bold text-sm',
              isServing ? 'bg-green-600 text-white' : 'bg-blue-100 text-blue-700'
            )}
          >
            {isServing ? <Zap size={18} /> : `#${token.position}`}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-900">{token.person_name}</span>
              <span
                className={clsx(
                  'badge',
                  isServing ? 'badge-serving' : 'badge-waiting'
                )}
              >
                {isServing ? 'Serving' : `Token ${token.token_number}`}
              </span>
            </div>
            {token.person_phone && (
              <p className="text-xs text-gray-500 mt-0.5">{token.person_phone}</p>
            )}
            <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Clock size={12} />
                Joined {new Date(token.joined_at).toLocaleTimeString()}
              </span>
              {token.estimated_wait_minutes !== null && isWaiting && (
                <span className="text-blue-600">
                  ~{token.estimated_wait_minutes}m wait
                </span>
              )}
              {token.actual_wait_minutes !== null && isServing && (
                <span className="text-green-700">
                  Waited {token.actual_wait_minutes}m
                </span>
              )}
            </div>
          </div>
        </div>

        {/* actions */}
        <div className="flex flex-col gap-1 items-end">
          {isServing && (
            <>
              <button
                className="btn-success text-xs py-1 px-2"
                disabled={busy}
                onClick={() =>
                  act(() => tokensApi.complete(queueId, token.id), 'Service completed!')
                }
              >
                <CheckCircle2 size={14} />
                Complete
              </button>
              <button
                className="btn-danger text-xs py-1 px-2"
                disabled={busy}
                onClick={() =>
                  act(() => tokensApi.cancel(queueId, token.id), 'Token cancelled')
                }
              >
                <XCircle size={14} />
                Cancel
              </button>
            </>
          )}
          {isWaiting && (
            <div className="flex gap-1">
              {!isFirst && (
                <button
                  className="p-1.5 rounded border border-gray-200 text-gray-500 hover:border-blue-400 hover:text-blue-600 disabled:opacity-40"
                  disabled={busy}
                  title="Move up"
                  onClick={() =>
                    act(() => tokensApi.moveUp(queueId, token.id), 'Moved up')
                  }
                >
                  <ArrowUp size={14} />
                </button>
              )}
              {!isLast && (
                <button
                  className="p-1.5 rounded border border-gray-200 text-gray-500 hover:border-blue-400 hover:text-blue-600 disabled:opacity-40"
                  disabled={busy}
                  title="Move down"
                  onClick={() =>
                    act(() => tokensApi.moveDown(queueId, token.id), 'Moved down')
                  }
                >
                  <ArrowDown size={14} />
                </button>
              )}
              <button
                className="p-1.5 rounded border border-gray-200 text-gray-500 hover:border-red-400 hover:text-red-600 disabled:opacity-40"
                disabled={busy}
                title="Cancel"
                onClick={() =>
                  act(() => tokensApi.cancel(queueId, token.id), 'Token cancelled')
                }
              >
                <XCircle size={14} />
              </button>
            </div>
          )}
          {busy && <Spinner size="sm" />}
        </div>
      </div>
    </div>
  );
}

export function QueuePage() {
  const { queueId } = useParams<{ queueId: string }>();
  const id = Number(queueId);

  const [queue, setQueue] = useState<Queue | null>(null);
  const [tokens, setTokens] = useState<Token[]>([]);
  const [loading, setLoading] = useState(true);
  const [callingNext, setCallingNext] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [personName, setPersonName] = useState('');
  const [personPhone, setPersonPhone] = useState('');
  const [adding, setAdding] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [q, t] = await Promise.all([queuesApi.get(id), tokensApi.list(id)]);
      setQueue(q);
      setTokens(t);
    } catch {
      // 403/404 handled by interceptor
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 5_000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const handleCallNext = async () => {
    setCallingNext(true);
    try {
      await tokensApi.callNext(id);
      toast.success('Next person called!');
      fetchAll();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || 'Failed to call next');
    } finally {
      setCallingNext(false);
    }
  };

  const handleAddPerson = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdding(true);
    try {
      await tokensApi.register(id, personName.trim(), personPhone.trim());
      toast.success(`${personName} added to queue!`);
      setPersonName('');
      setPersonPhone('');
      setShowAdd(false);
      fetchAll();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || 'Failed to add person');
    } finally {
      setAdding(false);
    }
  };

  const servingToken = tokens.find((t) => t.status === 'serving');
  const waitingTokens = tokens.filter((t) => t.status === 'waiting').sort((a, b) => (a.position ?? 0) - (b.position ?? 0));

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex justify-center items-center py-24">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (!queue) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-2xl mx-auto px-4 py-16 text-center">
          <p className="text-gray-500">Queue not found or access denied.</p>
          <Link to="/dashboard" className="btn-primary mt-4 inline-flex">Back to dashboard</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* breadcrumb */}
        <Link to="/dashboard" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6">
          <ArrowLeft size={14} />
          Back to dashboard
        </Link>

        {/* queue header */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{queue.name}</h1>
            {queue.description && <p className="text-gray-500 text-sm mt-1">{queue.description}</p>}
            <div className="flex items-center gap-4 mt-2 text-sm">
              <span className="flex items-center gap-1 text-yellow-700">
                <Users size={14} />
                <strong>{queue.waiting_count}</strong> waiting
              </span>
              {queue.serving_count > 0 && (
                <span className="flex items-center gap-1 text-green-700">
                  <Zap size={14} />
                  <strong>{queue.serving_count}</strong> serving
                </span>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <button
              className="btn-primary"
              onClick={() => setShowAdd(true)}
            >
              <UserPlus size={16} />
              Add Person
            </button>
            <button
              className="btn-success"
              onClick={handleCallNext}
              disabled={callingNext || !!servingToken || waitingTokens.length === 0}
              title={servingToken ? 'Complete current service first' : ''}
            >
              {callingNext ? <Spinner size="sm" /> : <PhoneCall size={16} />}
              Call Next
            </button>
          </div>
        </div>

        {/* add person form */}
        {showAdd && (
          <div className="card mb-6 border-blue-200 bg-blue-50">
            <h3 className="font-semibold mb-3 text-blue-900">Register person</h3>
            <form onSubmit={handleAddPerson} className="space-y-3">
              <input
                className="input"
                placeholder="Full name *"
                value={personName}
                onChange={(e) => setPersonName(e.target.value)}
                autoFocus
                required
              />
              <input
                className="input"
                placeholder="Phone number (optional)"
                value={personPhone}
                onChange={(e) => setPersonPhone(e.target.value)}
              />
              <div className="flex gap-2">
                <button type="submit" className="btn-primary" disabled={adding}>
                  {adding ? <Spinner size="sm" /> : <UserPlus size={16} />}
                  Add to Queue
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowAdd(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* currently serving */}
        {servingToken && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Now Serving
            </h2>
            <TokenCard
              token={servingToken}
              queueId={id}
              onRefresh={fetchAll}
              isFirst={true}
              isLast={true}
            />
          </div>
        )}

        {/* waiting list */}
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Waiting ({waitingTokens.length})
          </h2>
          {waitingTokens.length === 0 ? (
            <EmptyState
              icon={<Users size={40} />}
              title="No one waiting"
              description="Add a person to get the queue started."
            />
          ) : (
            <div className="space-y-3">
              {waitingTokens.map((t, idx) => (
                <TokenCard
                  key={t.id}
                  token={t}
                  queueId={id}
                  onRefresh={fetchAll}
                  isFirst={idx === 0}
                  isLast={idx === waitingTokens.length - 1}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
