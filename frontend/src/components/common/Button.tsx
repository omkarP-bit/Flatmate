import React from 'react';

type ButtonVariant = 'primary' | 'ghost' | 'danger' | 'outline';
type ButtonSize    = 'sm' | 'md';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
}

const VARIANT_STYLES: Record<ButtonVariant, React.CSSProperties> = {
  primary: { background: 'var(--accent-gradient)', backgroundSize: '200% 100%', color: '#0e0e0e', border: 'none', fontWeight: 500, boxShadow: 'var(--shadow-glow)', animation: 'fm-shimmer 4s linear infinite' },
  ghost:   { background: 'transparent', color: 'var(--text-secondary)', border: '0.5px solid var(--border-mid)' },
  danger:  { background: 'var(--bg-danger)', color: 'var(--text-danger)', border: '0.5px solid var(--danger-border)' },
  outline: { background: 'transparent', color: 'var(--text-primary)', border: '0.5px solid var(--border-heavy)' },
};

const SIZE_STYLES: Record<ButtonSize, React.CSSProperties> = {
  sm: { height: 28, padding: '0 12px', fontSize: 12, borderRadius: 8 },
  md: { height: 34, padding: '0 16px', fontSize: 13, borderRadius: 10 },
};

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  children,
  disabled,
  style,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        gap: 6, cursor: 'pointer', fontFamily: 'var(--font-sans)',
        transition: 'opacity 0.15s, transform 0.12s ease, box-shadow 0.2s ease',
        opacity: disabled || loading ? 0.5 : 1,
        ...VARIANT_STYLES[variant],
        ...SIZE_STYLES[size],
        ...style,
      }}
      onMouseDown={e => { const t = e.currentTarget; t.style.transform = 'scale(0.96)'; }}
      onMouseUp={e => { const t = e.currentTarget; t.style.transform = 'scale(1)'; }}
      onMouseLeave={e => { const t = e.currentTarget; t.style.transform = 'scale(1)'; }}
    >
      {icon && <span style={{ display: 'flex' }}>{icon}</span>}
      {loading ? 'Loading…' : children}
    </button>
  );
}