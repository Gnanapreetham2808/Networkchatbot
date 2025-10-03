import React from 'react';
import clsx from 'clsx';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  pulse?: boolean;
}

export function Skeleton({ className, pulse=true, ...rest }: SkeletonProps) {
  return <div className={clsx('bg-gray-200/70 dark:bg-gray-700/60 rounded-md', pulse && 'animate-pulse', className)} {...rest} />;
}

export function SkeletonText({ lines=3, className }: { lines?: number; className?: string }) {
  return (
    <div className={clsx('space-y-2', className)}>
      {Array.from({ length: lines }).map((_,i)=>(
        <Skeleton key={i} className="h-3 w-full" />
      ))}
    </div>
  );
}