interface LoaderProps {
  size?: number;
  fullPage?: boolean;
}

export default function Loader({ size = 24, fullPage = false }: LoaderProps) {
  const spinner = (
    <div style={{
      width: size, height: size,
      border: `2px solid var(--border-mid)`,
      borderTop: `2px solid var(--lime)`,
      borderRadius: '50%',
      animation: 'spin 0.7s linear infinite',
    }} />
  );

  if (fullPage) {
    return (
      <div style={{
        position: 'fixed', inset: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--bg-app)',
        zIndex: 999,
      }}>
        {spinner}
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <>
      {spinner}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </>
  );
}