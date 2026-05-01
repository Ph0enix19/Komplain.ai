// CommandCenter: first-screen operational overview for the demo.

function CommandCenter({
  cases,
  running,
  resolution,
  events,
  totalDuration,
  tone,
  setTone,
  traceStyle,
  setTraceStyle,
  onResolve,
  canResolve,
}) {
  const resolvedCount = cases.filter((caseItem) => caseItem.status === 'resolved').length;
  const reviewCount = cases.filter((caseItem) => caseItem.status === 'review' || caseItem.status === 'pending').length;
  const completedAgents = new Set(events.filter((event) => event.status === 'completed').map((event) => event.agent));
  const completion = events.length
    ? Math.round((window.AGENTS.filter((agent) => completedAgents.has(agent.key)).length / window.AGENTS.length) * 100)
    : 0;
  const latestResolution = resolution?.type || 'READY';
  const pipelineValue = running
    ? `${completion}%`
    : (totalDuration ? formatDurationMs(totalDuration) : 'Idle');

  return (
    <section className="command-center" aria-labelledby="command-title">
      <div className="command-main">
        <div className="command-kicker mono">
          <span className="command-pulse" aria-hidden="true"></span>
          Supervisor workspace
        </div>
        <h1 id="command-title">Resolve customer complaints with an auditable AI pipeline.</h1>
        <p className="command-copy">Run intake, context lookup, policy reasoning, bilingual drafting, and final human approval from one polished console.</p>
        <div className="command-actions">
          <button className="btn btn-primary command-cta" type="button" onClick={onResolve} disabled={!canResolve || running}>
            {running ? (
              <>
                <span className="spinner" aria-hidden="true"></span>
                Running agents
              </>
            ) : (
              <>
                Resolve current complaint
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M5 12h14M13 5l7 7-7 7" />
                </svg>
              </>
            )}
          </button>
          <span className="command-meta mono">{running ? `${completion}% pipeline complete` : `${cases.length} cases in view`}</span>
        </div>
      </div>

      <div className="command-controls" aria-label="Workflow controls">
        <div className="command-control">
          <span className="label">Reply tone</span>
          <SegmentedControl value={tone} onChange={setTone} options={[['formal', 'Formal'], ['friendly', 'Friendly'], ['technical', 'Technical']]} ariaLabel="Reply tone" />
        </div>
        <div className="command-control">
          <span className="label">Trace view</span>
          <SegmentedControl value={traceStyle} onChange={setTraceStyle} options={[['stepper', 'Stepper'], ['cards', 'Cards'], ['timeline', 'Timeline']]} ariaLabel="Trace layout" />
        </div>
      </div>

      <div className="command-metrics" aria-label="Dashboard metrics">
        <MetricTile label="Decision" value={latestResolution} tone={resolution?.requires_review ? 'warn' : 'primary'} icon="spark" />
        <MetricTile label="Resolved" value={String(resolvedCount)} tone="success" icon="check" />
        <MetricTile label="Review queue" value={String(reviewCount)} tone={reviewCount ? 'warn' : 'neutral'} icon="review" />
        <MetricTile label="Pipeline" value={pipelineValue} tone={running ? 'info' : (totalDuration ? 'success' : 'neutral')} icon="flow" />
      </div>
    </section>
  );
}

function MetricTile({ label, value, tone, icon }) {
  return (
    <div className={'metric-tile metric-' + tone}>
      <div className="metric-icon"><MetricIcon name={icon} /></div>
      <div>
        <div className="metric-value mono">{value}</div>
        <div className="metric-label">{label}</div>
      </div>
    </div>
  );
}

function MetricIcon({ name }) {
  const props = { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true };
  if (name === 'check') return <svg {...props}><path d="M20 6 9 17l-5-5" /></svg>;
  if (name === 'review') return <svg {...props}><path d="M12 9v4M12 17h.01" /><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /></svg>;
  if (name === 'flow') return <svg {...props}><path d="M4 6h7a4 4 0 0 1 4 4v8" /><path d="M4 18h16M18 16l2 2-2 2" /><circle cx="4" cy="6" r="2" /></svg>;
  return <svg {...props}><path d="M13 2 3 14h8l-1 8 11-14h-8l1-6z" /></svg>;
}

Object.assign(window, { CommandCenter });
