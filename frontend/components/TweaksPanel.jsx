// Tweaks panel (bottom-right) — theme / density / tone / trace style
function TweaksPanel({ open, setOpen, theme, setTheme, density, setDensity, tone, setTone, traceStyle, setTraceStyle }) {
  if (!open) return null;
  return (
    <div className="tweaks-panel">
      <div className="tweaks-head">
        <div className="tweaks-title">
          <div className="tweaks-dot"></div>
          <span>Tweaks</span>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={() => setOpen(false)} aria-label="Close">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <div className="tweaks-body">
        <TweakRow label="Theme">
          <SegmentedControl value={theme} onChange={setTheme} options={[['light','Light'],['dark','Dark']]} />
        </TweakRow>
        <TweakRow label="Density">
          <SegmentedControl value={density} onChange={setDensity} options={[['comfortable','Comfortable'],['compact','Compact']]} />
        </TweakRow>
        <TweakRow label="Reply tone">
          <SegmentedControl value={tone} onChange={setTone} options={[['formal','Formal'],['friendly','Friendly'],['technical','Technical']]} />
        </TweakRow>
        <TweakRow label="Trace layout" stack>
          <SegmentedControl value={traceStyle} onChange={setTraceStyle} options={[['stepper','Stepper'],['cards','Cards'],['timeline','Timeline']]} />
        </TweakRow>
      </div>
    </div>
  );
}

function TweakRow({ label, children, stack }) {
  return (
    <div className={'tweak-row' + (stack ? ' tweak-stack' : '')}>
      <span className="label" style={{margin:0}}>{label}</span>
      {children}
    </div>
  );
}

Object.assign(window, { TweaksPanel });
