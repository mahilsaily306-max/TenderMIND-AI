import { useEffect, useState } from 'react';
import { useAuth } from '../lib/auth';
import api from '../lib/api';
import type { Tender, User, Workspace } from '../types';
import { useNavigate } from 'react-router-dom';
import NotificationBell from '../components/NotificationBell';
import {
  LogOut, Sun, Moon, Plus, Users, Building2, FileText, CheckCircle,
  Clock, BarChart3, ExternalLink
} from 'lucide-react';

export default function OwnerDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [darkMode, setDarkMode] = useState(() => document.documentElement.classList.contains('dark'));

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  useEffect(() => {
    if (!user || user.role !== 'owner') {
      navigate('/login');
      return;
    }
    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      const [tendersRes, usersRes, workspacesRes] = await Promise.all([
        api.get('/tenders'),
        api.get('/users'),
        api.get('/workspaces'),
      ]);
      setTenders(tendersRes.data);
      setUsers(usersRes.data);
      setWorkspaces(workspacesRes.data);
    } catch (err) {
      console.error('Failed to load data', err);
    }
  };

  const stats = {
    total: tenders.length,
    active: tenders.filter((t) => ['identified', 'qualification', 'in_progress', 'internal_review'].includes(t.status)).length,
    submitted: tenders.filter((t) => t.status === 'submitted').length,
    won: tenders.filter((t) => t.status === 'won').length,
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-brand-600">TenderPilot AI</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {user.full_name} <span className="uppercase text-xs ml-1 px-1.5 py-0.5 rounded bg-brand-100 dark:bg-brand-900 text-brand-700 dark:text-brand-300">Owner</span>
            </span>
            <NotificationBell />
            <button onClick={() => setDarkMode(!darkMode)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button onClick={logout} className="flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-950 rounded-lg">
              <LogOut size={16} /> Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard icon={FileText} label="Total Tenders" value={stats.total} color="text-blue-600" />
          <StatCard icon={Clock} label="In Progress" value={stats.active} color="text-amber-600" />
          <StatCard icon={CheckCircle} label="Submitted" value={stats.submitted} color="text-green-600" />
          <StatCard icon={BarChart3} label="Won" value={stats.won} color="text-purple-600" />
        </div>

        {/* Users */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2"><Users size={20} /> Users</h2>
            <button className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700">
              <Plus size={16} /> Add User
            </button>
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Name</th>
                  <th className="text-left px-4 py-3 font-medium">Email</th>
                  <th className="text-left px-4 py-3 font-medium">Role</th>
                  <th className="text-left px-4 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-4 py-3">{u.full_name}</td>
                    <td className="px-4 py-3 text-gray-500">{u.email}</td>
                    <td className="px-4 py-3">
                      <RoleBadge role={u.role} />
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 text-xs ${u.is_active ? 'text-green-600' : 'text-red-600'}`}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Workspaces */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2"><Building2 size={20} /> Workspaces</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {workspaces.map((w) => (
              <div key={w.id} className="bg-white dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-800 shadow-sm">
                <h3 className="font-medium">{w.name}</h3>
                {w.description && <p className="text-sm text-gray-500 mt-1">{w.description}</p>}
              </div>
            ))}
          </div>
        </section>

        {/* Recent Tenders */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2"><FileText size={20} /> Recent Tenders</h2>
            <button
              onClick={() => navigate('/tenders/new')}
              className="flex items-center gap-1 text-sm bg-brand-600 text-white px-3 py-1.5 rounded-lg hover:bg-brand-700"
            >
              <Plus size={16} /> New Tender
            </button>
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Title</th>
                  <th className="text-left px-4 py-3 font-medium">Status</th>
                  <th className="text-left px-4 py-3 font-medium">Deadline</th>
                  <th className="text-left px-4 py-3 font-medium">Value</th>
                  <th className="text-left px-4 py-3 font-medium"> </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {tenders.slice(0, 10).map((t) => (
                  <tr key={t.id} className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer" onClick={() => navigate(`/tenders/${t.id}`)}>
                    <td className="px-4 py-3 font-medium">{t.title}</td>
                    <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                    <td className="px-4 py-3 text-gray-500">{t.bid_deadline ? new Date(t.bid_deadline).toLocaleDateString() : '-'}</td>
                    <td className="px-4 py-3">{t.estimated_value ? `$${t.estimated_value.toLocaleString()}` : '-'}</td>
                    <td className="px-4 py-3"><ExternalLink size={14} className="text-gray-400" /></td>
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

function StatCard({ icon: Icon, label, value, color }: { icon: any; label: string; value: number; color: string }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
      <div className="flex items-center gap-3">
        <div className={`p-3 rounded-lg bg-gray-100 dark:bg-gray-800 ${color}`}>
          <Icon size={24} />
        </div>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
        </div>
      </div>
    </div>
  );
}

function RoleBadge({ role }: { role: string }) {
  const colors: Record<string, string> = {
    owner: 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300',
    manager: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
    employee: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300',
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[role] || colors.employee}`}>
      {role}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    identified: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300',
    qualification: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
    in_progress: 'bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300',
    internal_review: 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300',
    submitted: 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300',
    won: 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300',
    lost: 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300',
    withdrawn: 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400',
  };
  const labels: Record<string, string> = {
    identified: 'Identified',
    qualification: 'Qualification',
    in_progress: 'In Progress',
    internal_review: 'Internal Review',
    submitted: 'Submitted',
    won: 'Won',
    lost: 'Lost',
    withdrawn: 'Withdrawn',
  };
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium ${colors[status] || ''}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${status === 'won' ? 'bg-emerald-500' : status === 'lost' ? 'bg-red-500' : status === 'submitted' ? 'bg-green-500' : 'bg-current'}`} />
      {labels[status] || status}
    </span>
  );
}
