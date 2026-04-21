// Topbar + header chrome
const { useState } = React;

function Topbar({ theme, setTheme, density, setDensity, tone, setTone, traceStyle, setTraceStyle, showTweaksUI }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="logo">
          <div className="logo-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none">
              <rect x="2.5" y="2.5" width="19" height="19" rx="5" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M7 9.5h10M7 13h7M9 16.5l-2 2.5V16.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="17" cy="8" r="2" fill="var(--accent)" stroke="var(--bg-elev)" strokeWidth="1"/>
            </svg>
          </div>
          <div className="logo-text">
            <div className="logo-name">Komplain<span style={{color:'var(--accent)'}}>.ai</span></div>
            <div className="logo-sub mono">agentic complaint resolution · v0.1</div>
          </div>
        </div>
      </div>
      <div className="topbar-center">
        <div className="pipeline-status">
          <span className="status-dot" style={{background:'var(--accent)'}}></span>
          <span className="mono" style={{fontSize:11}}>GLM-4 · ap-southeast-2 · 47 ms</span>
          <span className="divider-v"></span>
          <span className="mono" style={{fontSize:11, color:'var(--fg-muted)'}}>sambal&silk · seller_id 2047</span>
        </div>
      </div>
      <div className="topbar-right">
        {showTweaksUI && (
          <div className="tweaks-inline">
            <SegmentedControl value={theme} onChange={setTheme} options={[['light','Light'],['dark','Dark']]} />
          </div>
        )}
        <button className="btn btn-ghost" title="Docs">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/></svg>
          Docs
        </button>
        <div className="avatar mono" title="Nadia · Sambal & Silk">N</div>
      </div>
    </header>
  );
}

function SegmentedControl({ value, onChange, options }) {
  return (
    <div className="seg">
      {options.map(([val, label]) => (
        <button key={val}
          className={'seg-btn ' + (value === val ? 'seg-active' : '')}
          onClick={() => onChange(val)}>{label}</button>
      ))}
    </div>
  );
}

Object.assign(window, { Topbar, SegmentedControl });
