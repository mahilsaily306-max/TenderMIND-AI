import { type ReactNode } from 'react';
import { cn } from '../../lib/utils';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 px-6 text-center', className)}>
      <div className="mb-4 text-neutral-300 dark:text-neutral-600">
        {icon || <Inbox size={48} strokeWidth={1.5} />}
      </div>
      <h3 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-neutral-500 dark:text-neutral-400 max-w-sm mb-4">{description}</p>
      )}
      {action && <div>{action}</div>}
    </div>
  );
}
