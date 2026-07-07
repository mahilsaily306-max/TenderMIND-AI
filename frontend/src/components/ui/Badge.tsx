import { type ReactNode } from 'react';
import { cn } from '../../lib/utils';

type BadgeIntent = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';

interface BadgeProps {
  children: ReactNode;
  intent?: BadgeIntent;
  size?: 'sm' | 'md';
  dot?: boolean;
  className?: string;
}

const intentStyles: Record<BadgeIntent, string> = {
  default: 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300',
  success: 'bg-success-50 dark:bg-success-950 text-success-700 dark:text-success-300',
  warning: 'bg-warning-50 dark:bg-warning-950 text-warning-700 dark:text-warning-300',
  danger: 'bg-danger-50 dark:bg-danger-950 text-danger-700 dark:text-danger-300',
  info: 'bg-brand-50 dark:bg-brand-950 text-brand-700 dark:text-brand-300',
  neutral: 'bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400',
};

const dotColors: Record<BadgeIntent, string> = {
  default: 'bg-neutral-400',
  success: 'bg-success-500',
  warning: 'bg-warning-500',
  danger: 'bg-danger-500',
  info: 'bg-brand-500',
  neutral: 'bg-neutral-400',
};

export function Badge({ children, intent = 'default', size = 'sm', dot, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-medium rounded-full whitespace-nowrap',
        size === 'sm' ? 'px-2 py-0.5 text-2xs' : 'px-2.5 py-1 text-xs',
        intentStyles[intent],
        className,
      )}
    >
      {dot && <span className={cn('w-1.5 h-1.5 rounded-full', dotColors[intent])} />}
      {children}
    </span>
  );
}

// Convenience: Tender status → Badge
const statusIntent: Record<string, BadgeIntent> = {
  identified: 'neutral',
  qualification: 'info',
  in_progress: 'warning',
  internal_review: 'info',
  submitted: 'success',
  won: 'success',
  lost: 'danger',
  withdrawn: 'neutral',
};

const statusLabels: Record<string, string> = {
  identified: 'Identified',
  qualification: 'Qualification',
  in_progress: 'In Progress',
  internal_review: 'Internal Review',
  submitted: 'Submitted',
  won: 'Won',
  lost: 'Lost',
  withdrawn: 'Withdrawn',
};

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  return (
    <Badge intent={statusIntent[status] || 'default'} dot className={className}>
      {statusLabels[status] || status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
    </Badge>
  );
}

// Task priority → Badge
const priorityIntent: Record<string, BadgeIntent> = {
  low: 'neutral',
  medium: 'info',
  high: 'warning',
  urgent: 'danger',
};

export function PriorityBadge({ priority, className }: { priority: string; className?: string }) {
  return (
    <Badge intent={priorityIntent[priority] || 'default'} className={className}>
      {priority.charAt(0).toUpperCase() + priority.slice(1)}
    </Badge>
  );
}

// User role → Badge
const roleIntent: Record<string, BadgeIntent> = {
  owner: 'info',
  manager: 'success',
  employee: 'neutral',
};

export function RoleBadge({ role, className }: { role: string; className?: string }) {
  return (
    <Badge intent={roleIntent[role] || 'default'} className={className}>
      {role.charAt(0).toUpperCase() + role.slice(1)}
    </Badge>
  );
}
