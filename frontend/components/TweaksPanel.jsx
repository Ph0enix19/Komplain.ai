// Tweaks panel used by the external edit-mode host

function TweaksPanel({ open, setOpen, theme, setTheme, density, setDensity, tone, setTone, traceStyle, setTraceStyle }) {
  if (!open) return null;

  return (
    <div className="tweaks-panel" role="dialog" aria-label="Interface tweaks">
      <div className="tweaks-head">
        <div className="tweaks-title">
          <div className="tweaks-dot" aria-hidden="true"></div>
          <span>Tweaks</span>
        </div>
        <button className="btn btn-ghost btn-sm" type="button" onClick={() => setOpen(false)} aria-label="Close tweaks">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div className="tweaks-body">
        <TweakRow label="Theme">
          <SegmentedControl value={theme} onChange={setTheme} options={[['light', 'Light'], ['dark', 'Dark']]} ariaLabel="Theme" />
        </TweakRow>
        <TweakRow label="Density">
          <SegmentedControl value={density} onChange={setDensity} options={[['comfortable', 'Roomy'], ['compact', 'Tight']]} ariaLabel="Density" />
        </TweakRow>
        <TweakRow label="Reply tone">
          <SegmentedControl value={tone} onChange={setTone} options={[['formal', 'Formal'], ['friendly', 'Friendly'], ['technical', 'Technical']]} ariaLabel="Reply tone" />
        </TweakRow>
        <TweakRow label="Trace layout" stack>
          <SegmentedControl value={traceStyle} onChange={setTraceStyle} options={[['stepper', 'Stepper'], ['cards', 'Cards'], ['timeline', 'Timeline']]} ariaLabel="Trace layout" />
        </TweakRow>
      </div>
    </div>
  );
}

function TweakRow({ label, children, stack }) {
  return (
    <div className={'tweak-row' + (stack ? ' tweak-stack' : '')}>
      <span className="label">{label}</span>
      {children}
    </div>
  );
}

Object.assign(window, { TweaksPanel });
