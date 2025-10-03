import React from 'react';
import clsx from 'clsx';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'outline' | 'success' | 'danger' | 'warning' | 'neutral';
  size?: 'sm' | 'md';
  children: React.ReactNode;
}

const base = 'inline-flex items-center font-medium rounded-full border transition-colors select-none whitespace-nowrap';
const sizeMap = {
  sm: 'text-[10px] px-2 py-0.5 h-5',
  md: 'text-xs px-2.5 py-1 h-6'
};
const variantMap = {
  default: 'bg-gray-900 text-white border-gray-900',
  outline: 'bg-white text-gray-800 border-gray-300',
  success: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  danger: 'bg-rose-100 text-rose-700 border-rose-300',
  warning: 'bg-amber-100 text-amber-700 border-amber-300',
  neutral: 'bg-gray-100 text-gray-700 border-gray-200'
};

export function Badge({ variant='default', size='sm', className, children, ...rest }: BadgeProps) {
  return (
    <span
      className={clsx(base, sizeMap[size], variantMap[variant], className)}
      {...rest}
    >
      {children}
    </span>
  );
}
