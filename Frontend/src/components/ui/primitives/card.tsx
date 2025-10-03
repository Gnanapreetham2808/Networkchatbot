import React from 'react';
import clsx from 'clsx';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: 'none' | 'sm' | 'md' | 'lg';
  interactive?: boolean;
  glow?: boolean;
}

const padMap = {
  none: 'p-0',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-8'
};

export function Card({ padding='md', interactive=false, glow=false, className, children, ...rest }: CardProps) {
  return (
    <div
      className={clsx(
        'relative rounded-xl border bg-white/80 backdrop-blur-sm border-gray-200 shadow-sm',
        padMap[padding],
        interactive && 'transition hover:shadow-lg hover:-translate-y-0.5 cursor-pointer',
        glow && 'before:absolute before:inset-0 before:-z-10 before:rounded-[inherit] before:bg-gradient-to-br before:from-gray-200 before:to-transparent',
        className
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('mb-3', className)} {...rest} />;
}
export function CardTitle({ className, ...rest }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={clsx('text-sm font-semibold tracking-wide text-gray-900', className)} {...rest} />;
}
export function CardSubtitle({ className, ...rest }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={clsx('text-xs text-gray-500', className)} {...rest} />;
}
export function CardContent({ className, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('text-sm text-gray-700 space-y-2', className)} {...rest} />;
}
export function CardFooter({ className, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500', className)} {...rest} />;
}
