type BadgeVariant = 'neutral' | 'success' | 'danger' | 'warning' | 'info' | 'lime';

const VARIANTS: Record<BadgeVariant, { bg: string; color: string }> = {
  neutral: { bg: 'var(--bg-secondary)', color: 'var(--text-secondary)' },
  success: { bg: 'var(--bg-success)', color: 'var(--text-success)' },
  danger:  { bg: 'var(--bg-danger)', color: 'var(--text-danger)' },
  warning: { bg: 'var(--bg-warning)', color: 'var(--text-warning)' },
  info:    { bg: 'var(--bg-info)', color: 'var(--text-info)' },
  lime:    { bg: 'var(--lime-dim)', color: 'var(--lime-text)' },
};

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
}

export default function Badge({ label, variant = 'neutral' }: BadgeProps) {
  const v = VARIANTS[variant];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      padding: '2px 9px', borderRadius: 9999,
      fontSize: 11, fontWeight: 500,
      background: v.bg, color: v.color,
      whiteSpace: 'nowrap',
    }}>
      {label}
    </span>
  );
}