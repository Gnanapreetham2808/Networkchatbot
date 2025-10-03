import React from 'react';
import clsx from 'clsx';

interface SectionProps extends React.HTMLAttributes<HTMLElement> {
  bleed?: boolean;
  background?: 'none' | 'subtle' | 'dot';
  padding?: 'sm' | 'md' | 'lg' | 'xl';
}

const pad = { sm: 'py-8', md: 'py-12', lg: 'py-16', xl: 'py-24' };

export function Section({ bleed=false, background='none', padding='lg', className, children, ...rest }: SectionProps) {
  return (
    <section
      className={clsx(
        pad[padding],
        !bleed && 'relative',
        background === 'subtle' && 'bg-gray-50',
        background === 'dot' && 'bg-dot-grid [background-size:28px_28px]' ,
        className
      )}
      {...rest}
    >
      {children}
    </section>
  );
}
