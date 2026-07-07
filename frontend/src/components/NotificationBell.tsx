import { useEffect, useState, useRef } from 'react';
import api from '../lib/api';
import { Bell } from 'lucide-react';

interface Notification {
  id: number;
  type: string;
  title: string;
  message: string | null;
  is_read: boolean;
  reference_type: string | null;
  reference_id: number | null;
  created_at: string;
}

export default function NotificationBell() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadUnreadCount();
    const interval = setInterval(loadUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const loadUnreadCount = async () => {
    try {
      const res = await api.get('/notifications/unread-count');
      setUnreadCount(res.data.unread_count);
    } catch { /* ignore */ }
  };

  const toggleNotifications = async () => {
    if (!open) {
      try {
        const res = await api.get('/notifications?unread_only=true');
        setNotifications(res.data);
      } catch { /* ignore */ }
    }
    setOpen(!open);
  };

  const markRead = async (id: number) => {
    try {
      await api.post(`/notifications/${id}/read`);
      setNotifications(notifications.filter(n => n.id !== id));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch { /* ignore */ }
  };

  const markAllRead = async () => {
    try {
      await api.post('/notifications/read-all');
      setNotifications([]);
      setUnreadCount(0);
    } catch { /* ignore */ }
  };

  return (
    <div ref={ref} className="relative">
      <button onClick={toggleNotifications} className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
        <Bell size={18} />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-800 z-50">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800">
            <h3 className="text-sm font-semibold">Notifications</h3>
            {notifications.length > 0 && (
              <button onClick={markAllRead} className="text-xs text-brand-600 hover:text-brand-700">Mark all read</button>
            )}
          </div>
          <div className="max-h-72 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">No new notifications</p>
            ) : (
              notifications.map(n => (
                <div key={n.id} className="px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 border-b border-gray-100 dark:border-gray-800 last:border-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium">{n.title}</p>
                      {n.message && <p className="text-xs text-gray-500 mt-0.5">{n.message}</p>}
                      <p className="text-[10px] text-gray-400 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                    </div>
                    <button onClick={() => markRead(n.id)} className="text-[10px] text-gray-400 hover:text-brand-600 shrink-0">Dismiss</button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
