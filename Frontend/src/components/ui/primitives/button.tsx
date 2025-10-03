import React from 'react';
import clsx from 'clsx';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'solid' | 'outline' | 'ghost' | 'subtle';
  tone?: 'default' | 'primary' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
}

const sizeMap = {
  sm: 'h-8 px-3 text-xs rounded-md',
  md: 'h-10 px-4 text-sm rounded-lg',
  lg: 'h-11 px-6 text-sm rounded-lg'
};

const base = 'inline-flex items-center justify-center gap-2 font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none transition-all active:scale-[0.97]';

const toneStyles: Record<string, Record<string,string>> = {
  solid: {
    default: 'bg-gray-900 text-white hover:bg-gray-800',
    primary: 'bg-black text-white hover:bg-neutral-800',
    danger: 'bg-rose-600 text-white hover:bg-rose-500',
    success: 'bg-emerald-600 text-white hover:bg-emerald-500'
  },
  outline: {
    default: 'border border-gray-300 text-gray-800 hover:bg-gray-50',
    primary: 'border border-gray-900 text-gray-900 hover:bg-gray-100',
    danger: 'border border-rose-500 text-rose-600 hover:bg-rose-50',
    success: 'border border-emerald-600 text-emerald-700 hover:bg-emerald-50'
  },
  ghost: {
    default: 'text-gray-700 hover:bg-gray-100/70',
    primary: 'text-gray-900 hover:bg-gray-100',
    danger: 'text-rose-600 hover:bg-rose-50',
    success: 'text-emerald-600 hover:bg-emerald-50'
  },
  subtle: {
    default: 'bg-gray-100 text-gray-800 hover:bg-gray-200',
    primary: 'bg-gray-900/90 text-white hover:bg-gray-900',
    danger: 'bg-rose-100 text-rose-700 hover:bg-rose-200',
    success: 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
  }
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button({
  variant = 'solid',
  tone = 'primary',
  size = 'md',
  className,
  loading = false,
  icon,
  iconRight,
  children,
  ...rest
}, ref) {
  return (
    <button ref={ref} className={clsx(base, sizeMap[size], toneStyles[variant][tone], className)} disabled={loading || rest.disabled} {...rest}>
      {icon && <span className="shrink-0 inline-flex" aria-hidden>{icon}</span>}
      <span className={clsx('inline-flex items-center', loading && 'opacity-0')}>{children}</span>
      {iconRight && <span className="shrink-0 inline-flex" aria-hidden>{iconRight}</span>}
      {loading && (
        <span className="absolute inline-flex h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"/>
      )}
    </button>
  );
});
