import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../lib/utils';
import { Loader2 } from 'lucide-react';

const variants = {
  primary:
    'bg-brand-600 text-white hover:bg-brand-700 active:bg-brand-800 focus-visible:ring-brand-500 shadow-sm',
  secondary:
    'bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-200 border border-neutral-300 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-750 active:bg-neutral-100 dark:active:bg-neutral-700 focus-visible:ring-brand-500',
  ghost:
    'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 active:bg-neutral-200 dark:active:bg-neutral-700 focus-visible:ring-brand-500',
  danger:
    'bg-danger-600 text-white hover:bg-danger-700 active:bg-danger-800 focus-visible:ring-danger-500 shadow-sm',
};

const sizes = {
  sm: 'px-2.5 py-1.5 text-xs gap-1.5',
  md: 'px-3.5 py-2 text-sm gap-2',
  lg: 'px-5 py-2.5 text-base gap-2.5',
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
  loading?: boolean;
  icon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, disabled, icon, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-neutral-900',
          'disabled:opacity-50 disabled:pointer-events-none',
          variants[variant],
          sizes[size],
          className,
        )}
        {...props}
      >
        {loading ? <Loader2 size={size === 'sm' ? 14 : 16} className="animate-spin" /> : icon}
        {children && <span>{children}</span>}
      </button>
    );
  },
);

Button.displayName = 'Button';
