/**
 * Header.jsx — Imagio floating glass header bar.
 * Logo: abstracted aperture/lens monogram (copper stroke).
 * Status: quiet 6px jade dot + text, no glow/pulse.
 */
export default function Header({ isConnected }) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-mark">
          {/* Aperture monogram — custom SVG, 1.5px stroke */}
          <svg viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="9" />
            <line x1="12" y1="3" x2="12" y2="8" />
            <line x1="12" y1="16" x2="12" y2="21" />
            <line x1="3" y1="12" x2="8" y2="12" />
            <line x1="16" y1="12" x2="21" y2="12" />
            <circle cx="12" cy="12" r="3.5" />
          </svg>
        </div>
        <div>
          <div className="brand-name">Imagio</div>
          <div className="brand-tagline">Image Analysis Engine</div>
        </div>
      </div>

      <div className="header-status">
        <span className={`status-dot ${isConnected ? '' : 'offline'}`} />
        <span>{isConnected ? 'Operational' : 'Connecting'}</span>
      </div>
    </header>
  );
}
