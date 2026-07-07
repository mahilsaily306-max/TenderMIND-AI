import toast from 'react-hot-toast';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

const icons: Record<ToastType, typeof CheckCircle> = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

const colors: Record<ToastType, string> = {
  success: 'text-success-500',
  error: 'text-danger-500',
  warning: 'text-warning-500',
  info: 'text-brand-500',
};

export function showToast(message: string, type: ToastType = 'info') {
  const Icon = icons[type];
  toast.custom(
    (t) => (
      <div
        className={`${
          t.visible ? 'animate-slide-up' : 'opacity-0'
        } flex items-start gap-3 px-4 py-3 bg-white dark:bg-neutral-900 rounded-xl shadow-lg border border-neutral-200 dark:border-neutral-800 pointer-events-auto max-w-sm`}
      >
        <Icon size={18} className={colors[type]} />
        <p className="text-sm text-neutral-700 dark:text-neutral-300 flex-1">{message}</p>
        <button onClick={() => toast.dismiss(t.id)} className="text-neutral-400 hover:text-neutral-600">
          <X size={14} />
        </button>
      </div>
    ),
    { duration: 4000 },
  );
}
