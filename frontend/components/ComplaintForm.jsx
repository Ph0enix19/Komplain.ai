// ComplaintForm: intake panel for a new support case

function ComplaintForm({
  complaint,
  setComplaint,
  orderId,
  setOrderId,
  onResolve,
  running,
  scenarios,
  onScenario,
  activeScenario,
  modelLabel,
  agents,
}) {
  const hasComplaint = Boolean(complaint.trim());
  const agentCount = agents?.length || window.AGENTS.length;

  return (
    <aside className={'panel form-panel ' + (!hasComplaint ? 'form-panel-needs-input' : '')} aria-labelledby="complaint-form-title">
      <div className="panel-head">
        <div className="panel-title">
          <span className="panel-ix mono">01</span>
          <h2 id="complaint-form-title">New complaint</h2>
          <span className="mono subhead">Raw intake and optional order context</span>
        </div>
        <span className={'badge ' + (hasComplaint ? 'badge-accent' : 'badge-warn')}>{hasComplaint ? 'Ready' : 'Needs text'}</span>
      </div>

      <div className="scenario-row" aria-label="Quick-load complaint scenarios">
        <div className="label">Quick scenarios</div>
        <div className="scenario-chips">
          {scenarios.map((scenario) => (
            <button
              key={scenario.key}
              type="button"
              className={'chip ' + (scenario.key === activeScenario ? 'chip-active' : '')}
              onClick={() => onScenario(scenario)}
              disabled={running}
              aria-pressed={scenario.key === activeScenario}
            >
              <span className="chip-icon" aria-hidden="true"><ScenarioIcon name={scenario.key} /></span>
              <span className="chip-label">{scenario.label}</span>
              <span className="chip-sub mono">{scenario.blurb}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <label className="control-label" htmlFor="complaint-text">Customer complaint</label>
        <textarea
          id="complaint-text"
          className="textarea"
          rows={8}
          placeholder="Paste or type the customer's complaint in any language."
          value={complaint}
          onChange={(event) => setComplaint(event.target.value)}
          disabled={running}
          aria-invalid={!hasComplaint}
        />
        <div className="field-foot mono">
          <span>{complaint.length} chars</span>
          <span>Language auto-detected</span>
        </div>
        <div className="input-meter" aria-hidden="true">
          <span style={{ width: Math.min(100, Math.max(8, complaint.length / 3)) + '%' }}></span>
        </div>
      </div>

      <div className="field">
        <label className="control-label" htmlFor="order-id">
          Order ID <span className="optional-label">optional</span>
        </label>
        <input
          id="order-id"
          className="input mono"
          placeholder="ORD-2041"
          value={orderId}
          onChange={(event) => setOrderId(event.target.value)}
          disabled={running}
        />
        <div className="helper-text mono">Leave blank when the complaint already includes the order ID.</div>
      </div>

      <div className="form-foot">
        <button className="btn btn-primary btn-resolve" type="button" onClick={onResolve} disabled={running || !hasComplaint}>
          {running ? (
            <>
              <span className="spinner" aria-hidden="true"></span>
              Running pipeline
            </>
          ) : (
            <>
              Resolve complaint
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M5 12h14M13 5l7 7-7 7" />
              </svg>
            </>
          )}
        </button>
        <div className="form-foot-hint mono">{agentCount} agents - {modelLabel || 'configured model'} - live run</div>
      </div>
    </aside>
  );
}

function ScenarioIcon({ name }) {
  const props = { width: 15, height: 15, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round' };
  if (name === 'clean') return <svg {...props}><path d="M21 16V8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4a2 2 0 0 0 1-1.7z" /><path d="m3.3 7 8.7 5 8.7-5M12 22V12" /></svg>;
  if (name === 'edge') return <svg {...props}><path d="M12 9v4M12 17h.01" /><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /></svg>;
  return <svg {...props}><path d="M3 12h18M5 8h14M7 16h10" /><path d="M17 4l4 4-4 4" /></svg>;
}

Object.assign(window, { ComplaintForm });
