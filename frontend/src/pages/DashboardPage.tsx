import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { queuesApi } from '../api/queues';
import type { Queue } from '../types';
import { Navbar } from '../components/Navbar';
import { Spinner } from '../components/ui/Spinner';
import { EmptyState } from '../components/ui/EmptyState';
import toast from 'react-hot-toast';
import { Plus, Users, ChevronRight, Layers, Pencil, Trash2, X, Check } from 'lucide-react';

export function DashboardPage() {
  const [queues, setQueues] = useState<Queue[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');

  const fetchQueues = useCallback(async () => {
    try {
      const data = await queuesApi.list();
      setQueues(data);
    } catch {
      toast.error('Failed to load queues');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQueues();
    // poll every 10s to keep counts fresh
    const id = setInterval(fetchQueues, 10_000);
    return () => clearInterval(id);
  }, [fetchQueues]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const q = await queuesApi.create(newName.trim(), newDesc.trim());
      setQueues((prev) => [...prev, q]);
      setNewName('');
      setNewDesc('');
      setShowCreate(false);
      toast.success(`Queue "${q.name}" created`);
    } catch {
      toast.error('Failed to create queue');
    } finally {
      setCreating(false);
    }
  };

  const startEdit = (q: Queue) => {
    setEditingId(q.id);
    setEditName(q.name);
    setEditDesc(q.description);
  };

  const saveEdit = async (q: Queue) => {
    try {
      const updated = await queuesApi.update(q.id, editName.trim(), editDesc.trim());
      setQueues((prev) => prev.map((x) => (x.id === q.id ? updated : x)));
      setEditingId(null);
      toast.success('Queue updated');
    } catch {
      toast.error('Failed to update queue');
    }
  };

  const handleDelete = async (q: Queue) => {
    if (!confirm(`Delete queue "${q.name}"? All tokens will be deactivated.`)) return;
    try {
      await queuesApi.delete(q.id);
      setQueues((prev) => prev.filter((x) => x.id !== q.id));
      toast.success(`Queue "${q.name}" deleted`);
    } catch {
      toast.error('Failed to delete queue');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Your Queues</h1>
            <p className="text-gray-500 text-sm mt-1">Manage and monitor all your queues</p>
          </div>
          <button className="btn-primary" onClick={() => setShowCreate(true)}>
            <Plus size={16} />
            New Queue
          </button>
        </div>

        {/* create form */}
        {showCreate && (
          <div className="card mb-6 border-blue-200 bg-blue-50">
            <h3 className="font-semibold mb-4 text-blue-900">Create new queue</h3>
            <form onSubmit={handleCreate} className="space-y-3">
              <input
                className="input"
                placeholder="Queue name *"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                autoFocus
                required
              />
              <input
                className="input"
                placeholder="Description (optional)"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
              />
              <div className="flex gap-2">
                <button type="submit" className="btn-primary" disabled={creating}>
                  {creating ? <Spinner size="sm" /> : <Check size={16} />}
                  Create
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowCreate(false)}
                >
                  <X size={16} />
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* loading */}
        {loading && (
          <div className="flex justify-center py-16">
            <Spinner size="lg" />
          </div>
        )}

        {/* empty state */}
        {!loading && queues.length === 0 && (
          <EmptyState
            icon={<Layers size={56} />}
            title="No queues yet"
            description="Create your first queue to start managing people."
            action={
              <button className="btn-primary" onClick={() => setShowCreate(true)}>
                <Plus size={16} />
                Create your first queue
              </button>
            }
          />
        )}

        {/* queue cards */}
        {!loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {queues.map((q) => (
              <div key={q.id} className="card hover:shadow-md transition-shadow relative group">
                {editingId === q.id ? (
                  // edit form inline
                  <div className="space-y-2">
                    <input
                      className="input text-sm"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                    />
                    <input
                      className="input text-sm"
                      value={editDesc}
                      onChange={(e) => setEditDesc(e.target.value)}
                      placeholder="Description"
                    />
                    <div className="flex gap-2">
                      <button className="btn-primary text-xs py-1" onClick={() => saveEdit(q)}>
                        Save
                      </button>
                      <button className="btn-secondary text-xs py-1" onClick={() => setEditingId(null)}>
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-gray-900 truncate max-w-[180px]">{q.name}</h3>
                        {q.description && (
                          <p className="text-xs text-gray-500 mt-0.5 truncate max-w-[180px]">{q.description}</p>
                        )}
                      </div>
                      {/* action buttons — visible on hover */}
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => startEdit(q)}
                          className="p-1 text-gray-400 hover:text-blue-600 rounded"
                          title="Edit"
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          onClick={() => handleDelete(q)}
                          className="p-1 text-gray-400 hover:text-red-600 rounded"
                          title="Delete"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>

                    {/* stats */}
                    <div className="flex gap-4 text-sm mb-4">
                      <div className="flex items-center gap-1 text-yellow-700">
                        <Users size={14} />
                        <span className="font-medium">{q.waiting_count}</span>
                        <span className="text-gray-500">waiting</span>
                      </div>
                      {q.serving_count > 0 && (
                        <div className="flex items-center gap-1 text-green-700">
                          <span className="font-medium">{q.serving_count}</span>
                          <span className="text-gray-500">serving</span>
                        </div>
                      )}
                    </div>

                    <Link
                      to={`/queues/${q.id}`}
                      className="btn-primary w-full text-sm"
                    >
                      Manage Queue
                      <ChevronRight size={14} />
                    </Link>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
