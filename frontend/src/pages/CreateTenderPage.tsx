import { useState, useEffect, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import toast from 'react-hot-toast';
import type { Workspace } from '../types';
import { ArrowLeft } from 'lucide-react';

export default function CreateTenderPage() {
  const navigate = useNavigate();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    client_workspace_id: '',
    title: '',
    reference_number: '',
    description: '',
    bid_deadline: '',
    estimated_value: '',
    currency: 'USD',
  });

  useEffect(() => {
    api.get('/workspaces').then(res => setWorkspaces(res.data)).catch(() => toast.error('Failed to load workspaces'));
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.client_workspace_id || !form.title) {
      toast.error('Workspace and title are required');
      return;
    }
    setLoading(true);
    try {
      const res = await api.post('/tenders', {
        ...form,
        client_workspace_id: Number(form.client_workspace_id),
        estimated_value: form.estimated_value ? Number(form.estimated_value) : null,
        bid_deadline: form.bid_deadline || null,
      });
      toast.success('Tender created');
      navigate(`/tenders/${res.data.id}`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to create tender');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-xl font-bold">Create New Tender</h1>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-6 py-8">
        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-900 rounded-xl border shadow-sm p-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Workspace *</label>
              <select
                value={form.client_workspace_id}
                onChange={e => setForm({ ...form, client_workspace_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-transparent text-sm"
                required
              >
                <option value="">Select workspace...</option>
                {workspaces.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Title *</label>
              <input
                value={form.title}
                onChange={e => setForm({ ...form, title: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-transparent text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Reference Number</label>
              <input
                value={form.reference_number}
                onChange={e => setForm({ ...form, reference_number: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-transparent text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Bid Deadline</label>
              <input
                type="date"
                value={form.bid_deadline}
                onChange={e => setForm({ ...form, bid_deadline: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-transparent text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Estimated Value</label>
              <input
                type="number"
                value={form.estimated_value}
                onChange={e => setForm({ ...form, estimated_value: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-transparent text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Currency</label>
              <select
                value={form.currency}
                onChange={e => setForm({ ...form, currency: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-transparent text-sm"
              >
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={form.description}
                onChange={e => setForm({ ...form, description: e.target.value })}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-transparent text-sm resize-none"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button type="button" onClick={() => navigate(-1)} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="px-6 py-2 bg-brand-600 text-white rounded-lg text-sm hover:bg-brand-700 disabled:opacity-50">
              {loading ? 'Creating...' : 'Create Tender'}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
