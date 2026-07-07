import { type HTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../lib/utils';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  children: ReactNode;
}

const paddings = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export function Card({
  className,
  hoverable,
  padding = 'md',
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        'bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 shadow-sm',
        hoverable && 'transition-all duration-150 hover:shadow-md hover:border-neutral-300 dark:hover:border-neutral-700 cursor-pointer',
        paddings[padding],
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex items-center justify-between mb-4', className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn('text-base font-semibold text-neutral-900 dark:text-neutral-100', className)} {...props}>
      {children}
    </h3>
  );
}

export function CardContent({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn(className)} {...props}>
      {children}
    </div>
  );
}
