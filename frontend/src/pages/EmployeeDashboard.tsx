import { useEffect, useState } from 'react';
import { useAuth } from '../lib/auth';
import api from '../lib/api';
import type { Tender } from '../types';
import { useNavigate } from 'react-router-dom';
import NotificationBell from '../components/NotificationBell';
import { LogOut, Sun, Moon, ListTodo, Clock } from 'lucide-react';

export default function EmployeeDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [darkMode, setDarkMode] = useState(() => document.documentElement.classList.contains('dark'));

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  useEffect(() => {
    if (!user || user.role === 'owner') {
      navigate('/login');
      return;
    }
    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      const [tendersRes] = await Promise.all([api.get('/tenders')]);
      setTenders(tendersRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  if (!user) return null;

  const pending = tenders.filter((t) => t.status !== 'won' && t.status !== 'lost' && t.status !== 'withdrawn').length;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-brand-600">TenderPilot AI</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">{user.full_name} <span className="text-xs ml-1 px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-700">Employee</span></span>
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border shadow-sm">
            <div className="flex items-center gap-3">
              <ListTodo size={24} className="text-blue-600" />
              <div><p className="text-2xl font-bold">{tenders.length}</p><p className="text-sm text-gray-500">Assigned Tenders</p></div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border shadow-sm">
            <div className="flex items-center gap-3">
              <Clock size={24} className="text-amber-600" />
              <div><p className="text-2xl font-bold">{pending}</p><p className="text-sm text-gray-500">Active</p></div>
            </div>
          </div>
        </div>

        <section>
          <h2 className="text-lg font-semibold mb-4">My Tenders</h2>
          <div className="bg-white dark:bg-gray-900 rounded-xl border shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="text-left px-4 py-3">Title</th>
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="text-left px-4 py-3">Deadline</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {tenders.map((t) => (
                  <tr key={t.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-4 py-3 font-medium">{t.title}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium bg-gray-100 dark:bg-gray-800">
                        <span className="w-1.5 h-1.5 rounded-full bg-current" />
                        {t.status.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{t.bid_deadline ? new Date(t.bid_deadline).toLocaleDateString() : '-'}</td>
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
