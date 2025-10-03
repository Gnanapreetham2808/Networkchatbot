import React from 'react';
import clsx from 'clsx';

interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  width?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  center?: boolean;
}

const maxMap = {
  sm: 'max-w-screen-sm',
  md: 'max-w-screen-md',
  lg: 'max-w-screen-lg',
  xl: 'max-w-screen-xl',
  '2xl': 'max-w-screen-2xl',
  full: 'max-w-full'
};

export function Container({ width='xl', center=false, className, children, ...rest }: ContainerProps) {
  return (
    <div className={clsx('w-full mx-auto px-4 sm:px-6 lg:px-8', maxMap[width], center && 'text-center', className)} {...rest}>
      {children}
    </div>
  );
}
