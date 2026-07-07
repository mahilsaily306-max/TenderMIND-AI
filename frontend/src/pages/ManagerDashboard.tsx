import { useEffect, useState } from 'react';
import { useAuth } from '../lib/auth';
import api from '../lib/api';
import type { Tender, Workspace } from '../types';
import { useNavigate } from 'react-router-dom';
import NotificationBell from '../components/NotificationBell';
import { LogOut, Sun, Moon, FileText, Clock, BarChart3 } from 'lucide-react';

export default function ManagerDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [darkMode, setDarkMode] = useState(() => document.documentElement.classList.contains('dark'));

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  useEffect(() => {
    if (!user || user.role === 'employee') {
      navigate('/login');
      return;
    }
    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      const [tendersRes, workspacesRes] = await Promise.all([
        api.get('/tenders'),
        api.get('/workspaces'),
      ]);
      setTenders(tendersRes.data);
      setWorkspaces(workspacesRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  if (!user) return null;

  const active = tenders.filter((t) => !['won', 'lost', 'withdrawn'].includes(t.status)).length;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-brand-600">TenderPilot AI</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">{user.full_name} <span className="text-xs ml-1 px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900 text-blue-700">Manager</span></span>
          <NotificationBell />
          <button onClick={() => setDarkMode(!darkMode)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button onClick={logout} className="flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-950 rounded-lg">
            <LogOut size={16} /> Logout
          </button>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border shadow-sm">
            <div className="flex items-center gap-3">
              <FileText size={24} className="text-blue-600" />
              <div><p className="text-2xl font-bold">{tenders.length}</p><p className="text-sm text-gray-500">Total Tenders</p></div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border shadow-sm">
            <div className="flex items-center gap-3">
              <Clock size={24} className="text-amber-600" />
              <div><p className="text-2xl font-bold">{active}</p><p className="text-sm text-gray-500">Active</p></div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border shadow-sm">
            <div className="flex items-center gap-3">
              <BarChart3 size={24} className="text-purple-600" />
              <div><p className="text-2xl font-bold">{workspaces.length}</p><p className="text-sm text-gray-500">Workspaces</p></div>
            </div>
          </div>
        </div>

        <section>
          <h2 className="text-lg font-semibold mb-4">Your Tenders</h2>
          <div className="bg-white dark:bg-gray-900 rounded-xl border shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="text-left px-4 py-3">Title</th>
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="text-left px-4 py-3">Deadline</th>
                  <th className="text-left px-4 py-3">Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {tenders.map((t) => (
                  <tr key={t.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-4 py-3 font-medium">{t.title}</td>
                    <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                    <td className="px-4 py-3 text-gray-500">{t.bid_deadline ? new Date(t.bid_deadline).toLocaleDateString() : '-'}</td>
                    <td className="px-4 py-3">{t.estimated_value ? `$${t.estimated_value.toLocaleString()}` : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    identified: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
    qualification: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    in_progress: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300',
    internal_review: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
    submitted: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    won: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300',
    lost: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
    withdrawn: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400',
  };
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium ${colors[status] || ''}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {status.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
    </span>
  );
}
