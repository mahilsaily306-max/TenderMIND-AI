import { cn } from '../../lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
}

export function Skeleton({ className, variant = 'text' }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse-soft bg-neutral-200 dark:bg-neutral-800',
        variant === 'circular' ? 'rounded-full' : variant === 'rectangular' ? 'rounded-lg' : 'rounded h-4',
        className,
      )}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-6 space-y-4">
      <Skeleton className="h-5 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
}

export function TableSkeletonRows({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i}>
          {Array.from({ length: cols }).map((_, j) => (
            <td key={j} className="px-4 py-3">
              <Skeleton className="h-4" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}
