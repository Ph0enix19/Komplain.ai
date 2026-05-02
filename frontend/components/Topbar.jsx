// Topbar + global workspace controls

function Topbar({ theme, setTheme, density, setDensity, modelLabel }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="logo" aria-label="Komplain.ai">
          <div className="logo-mark" aria-hidden="true">
            <img className="logo-img" src="assets/app-logo.jpeg" alt="" />
          </div>
          <div className="logo-text">
            <div className="logo-name">Komplain<span className="logo-dot">.ai</span></div>
            <div className="logo-sub mono">agentic complaint resolution</div>
          </div>
        </div>
      </div>

      <div className="topbar-center">
        <div className="pipeline-status" role="status" aria-live="polite">
          <span className="status-dot" aria-hidden="true"></span>
          <span className="mono topbar-status-main">{modelLabel || 'configured model'} live API</span>
          <span className="divider-v" aria-hidden="true"></span>
          <span className="mono topbar-status-sub">supervised support workspace</span>
        </div>
      </div>

      <div className="topbar-right">
        <div className="topbar-controls">
          <SegmentedControl
            value={theme}
            onChange={setTheme}
            options={[['light', 'Light'], ['dark', 'Dark']]}
            ariaLabel="Theme"
          />
          <SegmentedControl
            value={density}
            onChange={setDensity}
            options={[['comfortable', 'Roomy'], ['compact', 'Tight']]}
            ariaLabel="Density"
          />
        </div>
        <a className="btn btn-ghost btn-sm" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer" title="Open API docs">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
            <path d="M14 3v5h5M9 13h6M9 17h4" />
          </svg>
          API docs
        </a>
        <div className="avatar mono" title="Komplain.ai workspace" aria-hidden="true">K</div>
      </div>
    </header>
  );
}

function SegmentedControl({ value, onChange, options, ariaLabel }) {
  return (
    <div className="seg" role="group" aria-label={ariaLabel}>
      {options.map(([val, label]) => (
        <button
          key={val}
          type="button"
          className={'seg-btn ' + (value === val ? 'seg-active' : '')}
          aria-pressed={value === val}
          onClick={() => onChange(val)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

Object.assign(window, { Topbar, SegmentedControl });
