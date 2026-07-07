import { type ReactNode, type TableHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

interface TableProps extends TableHTMLAttributes<HTMLTableElement> {
  children: ReactNode;
}

export function Table({ className, children, ...props }: TableProps) {
  return (
    <div className="w-full overflow-auto">
      <table className={cn('w-full text-sm', className)} {...props}>
        {children}
      </table>
    </div>
  );
}

export function TableHeader({ className, children, ...props }: TableHTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead className={cn('border-b border-neutral-200 dark:border-neutral-800', className)} {...props}>
      {children}
    </thead>
  );
}

export function TableBody({ className, children, ...props }: TableHTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody className={cn('divide-y divide-neutral-200 dark:divide-neutral-800', className)} {...props}>
      {children}
    </tbody>
  );
}

export function TableRow({ className, children, ...props }: TableHTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr className={cn('transition-colors hover:bg-neutral-50 dark:hover:bg-neutral-800/50', className)} {...props}>
      {children}
    </tr>
  );
}

export function TableHead({ className, children, ...props }: TableHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={cn(
        'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400',
        className,
      )}
      {...props}
    >
      {children}
    </th>
  );
}

export function TableCell({ className, children, ...props }: TableHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={cn('px-4 py-3 text-sm text-neutral-700 dark:text-neutral-300', className)} {...props}>
      {children}
    </td>
  );
}


