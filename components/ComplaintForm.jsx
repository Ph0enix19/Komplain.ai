// ComplaintForm — left column

function ComplaintForm({ complaint, setComplaint, orderId, setOrderId, onResolve, running, scenarios, onScenario }) {
  return (
    <aside className="panel form-panel">
      <div className="panel-head">
        <div className="panel-title">
          <span className="panel-ix mono">01</span>
          <h2>New complaint</h2>
        </div>
        <span className="badge">input</span>
      </div>

      <div className="scenario-row">
        <div className="label" style={{marginBottom: 8}}>Quick-load scenarios</div>
        <div className="scenario-chips">
          {scenarios.map(s => (
            <button key={s.key} className="chip" onClick={() => onScenario(s)} disabled={running}>
              <span className="chip-label">{s.label}</span>
              <span className="chip-sub mono">{s.blurb}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <label className="label">Customer complaint</label>
        <textarea
          className="textarea"
          rows={8}
          placeholder="Paste or type the customer's complaint in any language."
          value={complaint}
          onChange={e => setComplaint(e.target.value)}
          disabled={running}
        />
        <div className="field-foot mono">
          <span>{complaint.length} chars</span>
          <span>·</span>
          <span>lang: auto-detect</span>
        </div>
      </div>

      <div className="field">
        <label className="label">Order ID <span style={{color:'var(--fg-subtle)', textTransform:'none', fontWeight:400}}>· optional</span></label>
        <input
          className="input mono"
          placeholder="ORD-2041"
          value={orderId}
          onChange={e => setOrderId(e.target.value)}
          disabled={running}
        />
        <div className="field-foot mono">
          <span style={{color:'var(--fg-subtle)'}}>Leave blank if the order ID appears in the complaint.</span>
        </div>
      </div>

      <div className="form-foot">
        <button className="btn btn-primary btn-resolve" onClick={onResolve} disabled={running || !complaint.trim()}>
          {running ? (
            <>
              <span className="spinner"></span>
              Running pipeline...
            </>
          ) : (
            <>
              Resolve complaint
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
            </>
          )}
        </button>
        <div className="form-foot-hint mono">↵ 4 agents · GLM-5.1 · live run</div>
      </div>
    </aside>
  );
}

Object.assign(window, { ComplaintForm });
