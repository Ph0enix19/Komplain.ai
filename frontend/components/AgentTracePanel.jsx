// AgentTracePanel: live workflow trace with three presentation modes

function StatusIcon({ status }) {
  if (status === 'completed') {
    return (
      <span className="icon-wrap icon-done" aria-hidden="true">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 13l4 4L19 7" />
        </svg>
      </span>
    );
  }
  if (status === 'running' || status === 'started') {
    return <span className="icon-wrap icon-run" aria-hidden="true"><span className="spinner-sm"></span></span>;
  }
  if (status === 'failed') {
    return (
      <span className="icon-wrap icon-fail" aria-hidden="true">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
          <path d="M6 6l12 12M18 6 6 18" />
        </svg>
      </span>
    );
  }
  return <span className="icon-wrap icon-idle" aria-hidden="true"></span>;
}

function AgentStatus(events, agentKey) {
  const mine = events.filter((event) => event.agent === agentKey);
  if (!mine.length) return { status: 'idle', message: 'Waiting...', events: [], output: null };
  const last = mine[mine.length - 1];
  return {
    status: last.status,
    message: last.message,
    events: mine,
    output: mine.find((event) => event.output)?.output || null,
  };
}

function fmtTime(at) {
  return (at / 1000).toFixed(2) + 's';
}

function statusBadgeClass(status, isActive) {
  if (status === 'completed') return 'badge-accent';
  if (status === 'failed') return 'badge-danger';
  if (isActive) return 'badge-info';
  return '';
}

function TraceStepper({ events }) {
  return (
    <div className="trace trace-stepper">
      <div className="trace-rail" aria-hidden="true"></div>
      {window.AGENTS.map((agent, index) => {
        const state = AgentStatus(events, agent.key);
        const isActive = state.status === 'running' || state.status === 'started';
        const logLines = state.events.slice(-3);

        return (
          <div key={agent.key} className={'trace-step status-' + state.status + (isActive ? ' active' : '')}>
            <div className="trace-step-marker">
              <div className="trace-node"><StatusIcon status={state.status} /></div>
              <span className="trace-ix mono">0{index + 1}</span>
            </div>
            <div className="trace-step-head">
              <div className="trace-step-id">
                <div className="trace-step-name">{agent.name}</div>
                <div className="trace-step-role mono">{agent.role}</div>
              </div>
              <div className="trace-step-meta">
                <span className={'badge ' + statusBadgeClass(state.status, isActive)}>{state.status}</span>
                {state.events.length > 0 && (
                  <span className="mono trace-time">{fmtTime(state.events[state.events.length - 1].at)}</span>
                )}
              </div>
            </div>

            {logLines.length > 0 && (
              <div className="trace-log">
                {logLines.map((event, lineIndex) => (
                  <div key={lineIndex} className="log-line mono">
                    <span className="log-time">{fmtTime(event.at)}</span>
                    <span className={'log-dot status-' + event.status}></span>
                    <span className="log-msg">{event.message}</span>
                  </div>
                ))}
                {state.output && (
                  <details className="log-json">
                    <summary className="mono">output.json</summary>
                    <pre className="mono">{JSON.stringify(state.output, null, 2)}</pre>
                  </details>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function TraceCards({ events }) {
  return (
    <div className="trace trace-cards">
      {window.AGENTS.map((agent, index) => {
        const state = AgentStatus(events, agent.key);
        const isActive = state.status === 'running' || state.status === 'started';

        return (
          <div key={agent.key} className={'agent-card status-' + state.status + (isActive ? ' active' : '')}>
            <div className="agent-card-head">
              <span className="mono agent-card-ix">AGENT_0{index + 1}</span>
              <StatusIcon status={state.status} />
            </div>
            <div className="agent-card-name">{agent.name}</div>
            <div className="agent-card-role mono">{agent.role}</div>
            <div className="agent-card-body">
              {state.events.length === 0 && <div className="agent-card-idle mono">idle - awaiting upstream</div>}
              {state.events.slice(-2).map((event, lineIndex) => (
                <div key={lineIndex} className="mono log-line">
                  <span className="log-time">{fmtTime(event.at)}</span>
                  <span className={'log-dot status-' + event.status}></span>
                  <span className="log-msg">{event.message}</span>
                </div>
              ))}
            </div>
            {state.output && (
              <div className="agent-card-out mono">
                {Object.entries(state.output).slice(0, 3).map(([key, value]) => (
                  <div key={key} className="kv">
                    <span className="kv-k">{key}</span>
                    <span className="kv-v">{typeof value === 'object' ? JSON.stringify(value).slice(0, 28) : String(value).slice(0, 40)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function TraceTimeline({ events }) {
  const total = 6000;
  const maxAt = events.length ? Math.max(...events.map((event) => event.at)) : 100;
  const scale = Math.max(total, maxAt + 500);

  return (
    <div className="trace trace-timeline">
      <div className="tl-ruler mono" aria-hidden="true">
        {[0, 1, 2, 3, 4, 5, 6].map((second) => (
          <span key={second} style={{ left: `${(second * 1000 / scale) * 100}%` }}>{second}s</span>
        ))}
      </div>
      {window.AGENTS.map((agent, index) => {
        const state = AgentStatus(events, agent.key);
        const startAt = state.events[0]?.at;
        const endAt = state.events.find((event) => event.status === 'completed' || event.status === 'failed')?.at;
        const isActive = state.status === 'running' || state.status === 'started';

        return (
          <div key={agent.key} className={'tl-row status-' + state.status}>
            <div className="tl-label">
              <span className="mono trace-time">0{index + 1}</span>
              <div>
                <div className="tl-agent-name">{agent.name}</div>
                <div className="mono tl-agent-role">{agent.role}</div>
              </div>
            </div>
            <div className="tl-track">
              {startAt != null && (
                <div
                  className={'tl-bar ' + (isActive ? 'tl-bar-active' : '')}
                  style={{
                    left: `${(startAt / scale) * 100}%`,
                    width: `${(((endAt ?? (startAt + 300)) - startAt) / scale) * 100}%`,
                  }}
                >
                  <span className="tl-bar-msg mono">{state.message}</span>
                </div>
              )}
              {state.events.filter((event) => event.status === 'running').map((event, tickIndex) => (
                <div key={tickIndex} className="tl-tick mono" style={{ left: `${(event.at / scale) * 100}%` }} title={event.message}></div>
              ))}
            </div>
            <div className="tl-meta mono">
              {endAt ? fmtTime(endAt - startAt) : (isActive ? '...' : '-')}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AgentTracePanel({ events, running, traceStyle, totalDuration }) {
  const completedCount = window.AGENTS.filter((agent) => AgentStatus(events, agent.key).status === 'completed').length;
  const pct = running ? Math.min(95, (completedCount / 4) * 100) : (events.length ? 100 : 0);
  const supervisorLast = [...events].reverse().find((event) => event.agent === 'supervisor');

  return (
    <section className="panel trace-panel" aria-labelledby="agent-trace-title">
      <div className="panel-head">
        <div className="panel-title">
          <span className="panel-ix mono">02</span>
          <h2 id="agent-trace-title">Agent trace</h2>
          <span className="mono subhead">4-agent pipeline with supervisor validation</span>
        </div>
        <div className="panel-actions">
          {running && <span className="live-dot"><span className="live-dot-inner"></span>Live</span>}
          {!running && events.length > 0 && <span className="badge badge-accent">Resolved - {fmtTime(totalDuration || 0)}</span>}
          {!running && events.length === 0 && <span className="badge">Idle</span>}
        </div>
      </div>

      <div className="trace-panel-body" aria-live="polite">
        <div className="trace-progress" aria-label="Pipeline progress">
          <div className="trace-progress-bar" style={{ width: pct + '%' }}></div>
        </div>

        {supervisorLast && (
          <div className="supervisor-line mono">
            <span className="sup-tag">Supervisor</span>
            <span>{supervisorLast.message}</span>
          </div>
        )}

        {events.length === 0 && !running && (
          <div className="trace-empty">
            <EmptyIllustration />
            <div className="empty-title">Pipeline idle</div>
            <div className="empty-sub">Submit a complaint or choose a scenario to run the full agent workflow.</div>
          </div>
        )}

        {(events.length > 0 || running) && (
          <>
            {traceStyle === 'cards' && <TraceCards events={events} />}
            {traceStyle === 'timeline' && <TraceTimeline events={events} />}
            {traceStyle === 'stepper' && <TraceStepper events={events} />}
          </>
        )}
      </div>
    </section>
  );
}

function EmptyIllustration() {
  return (
    <svg width="120" height="90" viewBox="0 0 120 90" fill="none" aria-hidden="true">
      <rect x="10" y="18" width="100" height="54" rx="10" stroke="var(--border-strong)" strokeWidth="1.2" fill="var(--surface-inset)" />
      {[0, 1, 2, 3].map((index) => (
        <g key={index}>
          <circle cx={24 + index * 24} cy="45" r="5.5" fill="var(--surface)" stroke="var(--border-strong)" strokeWidth="1.2" />
          {index < 3 && <line x1={29.5 + index * 24} y1="45" x2={42.5 + index * 24} y2="45" stroke="var(--border-strong)" strokeWidth="1.2" strokeDasharray="2 2" />}
        </g>
      ))}
      <circle cx="24" cy="45" r="2" fill="var(--color-primary)" opacity="0.75" />
    </svg>
  );
}

Object.assign(window, { AgentTracePanel, StatusIcon });
