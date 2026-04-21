// AgentTracePanel — the hero. 3 style variants (tweakable).

function StatusIcon({ status }) {
  if (status === 'completed') {
    return (
      <span className="icon-wrap icon-done">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M5 13l4 4L19 7"/></svg>
      </span>
    );
  }
  if (status === 'running' || status === 'started') {
    return <span className="icon-wrap icon-run"><span className="spinner-sm"></span></span>;
  }
  if (status === 'failed') {
    return <span className="icon-wrap icon-fail"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></span>;
  }
  return <span className="icon-wrap icon-idle"></span>;
}

function AgentStatus(events, agentKey) {
  const mine = events.filter(e => e.agent === agentKey);
  if (!mine.length) return { status: 'idle', message: 'Waiting...', events: [], output: null };
  const last = mine[mine.length - 1];
  return { status: last.status, message: last.message, events: mine, output: mine.find(e => e.output)?.output || null };
}

function fmtTime(at) {
  const s = (at / 1000).toFixed(2);
  return s + 's';
}

// --------- Variant A: Stepper (default) — vertical, terminal log under each step
function TraceStepper({ events, running, onOpenDetail }) {
  return (
    <div className="trace trace-stepper">
      <div className="trace-rail"></div>
      {window.AGENTS.map((agent, i) => {
        const st = AgentStatus(events, agent.key);
        const isActive = st.status === 'running' || st.status === 'started';
        const logLines = st.events.slice(-3);
        return (
          <div key={agent.key} className={'trace-step status-' + st.status + (isActive ? ' active' : '')}>
            <div className="trace-step-head">
              <div className="trace-step-marker">
                <div className="trace-node"><StatusIcon status={st.status} /></div>
                <span className="trace-ix mono">0{i+1}</span>
              </div>
              <div className="trace-step-id">
                <div className="trace-step-name">{agent.name}</div>
                <div className="trace-step-role mono">{agent.role}</div>
              </div>
              <div className="trace-step-meta">
                <span className={'badge ' + (st.status === 'completed' ? 'badge-accent' : st.status === 'failed' ? 'badge-danger' : isActive ? 'badge-info' : '')}>
                  {st.status}
                </span>
                {st.events.length > 0 && <span className="mono" style={{fontSize:11, color:'var(--fg-subtle)'}}>{fmtTime(st.events[st.events.length-1].at)}</span>}
              </div>
            </div>
            {logLines.length > 0 && (
              <div className="trace-log">
                {logLines.map((e, ix) => (
                  <div key={ix} className="log-line mono">
                    <span className="log-time">{fmtTime(e.at)}</span>
                    <span className={'log-dot status-' + e.status}></span>
                    <span className="log-msg">{e.message}</span>
                  </div>
                ))}
                {st.output && (
                  <details className="log-json">
                    <summary className="mono">output.json</summary>
                    <pre className="mono">{JSON.stringify(st.output, null, 2)}</pre>
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

// --------- Variant B: Card stack — horizontally richer, each agent is a card
function TraceCards({ events }) {
  return (
    <div className="trace trace-cards">
      {window.AGENTS.map((agent, i) => {
        const st = AgentStatus(events, agent.key);
        const isActive = st.status === 'running' || st.status === 'started';
        return (
          <div key={agent.key} className={'agent-card status-' + st.status + (isActive ? ' active' : '')}>
            <div className="agent-card-head">
              <span className="mono agent-card-ix">AGENT_0{i+1}</span>
              <StatusIcon status={st.status} />
            </div>
            <div className="agent-card-name">{agent.name}</div>
            <div className="agent-card-role">{agent.role}</div>
            <div className="agent-card-body">
              {st.events.length === 0 && <div className="agent-card-idle mono">idle · awaiting upstream</div>}
              {st.events.slice(-2).map((e, ix) => (
                <div key={ix} className="mono log-line">
                  <span className="log-time">{fmtTime(e.at)}</span>
                  <span className={'log-dot status-' + e.status}></span>
                  <span className="log-msg">{e.message}</span>
                </div>
              ))}
            </div>
            {st.output && (
              <div className="agent-card-out mono">
                {Object.entries(st.output).slice(0, 3).map(([k, v]) => (
                  <div key={k} className="kv">
                    <span className="kv-k">{k}</span>
                    <span className="kv-v">{typeof v === 'object' ? JSON.stringify(v).slice(0, 28) : String(v).slice(0, 40)}</span>
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

// --------- Variant C: Timeline — horizontal progress bar + expandable rows
function TraceTimeline({ events, running }) {
  const total = 6000; // ms for layout — scale based on max event
  const maxAt = events.length ? Math.max(...events.map(e => e.at)) : 100;
  const scale = Math.max(total, maxAt + 500);
  return (
    <div className="trace trace-timeline">
      <div className="tl-ruler mono">
        {[0,1,2,3,4,5,6].map(s => <span key={s} style={{left: `${(s*1000/scale)*100}%`}}>{s}s</span>)}
      </div>
      {window.AGENTS.map((agent, i) => {
        const st = AgentStatus(events, agent.key);
        const startAt = st.events[0]?.at;
        const endAt = st.events.find(e => e.status === 'completed' || e.status === 'failed')?.at;
        const isActive = st.status === 'running' || st.status === 'started';
        return (
          <div key={agent.key} className={'tl-row status-' + st.status}>
            <div className="tl-label">
              <span className="mono" style={{color:'var(--fg-subtle)', fontSize:11}}>0{i+1}</span>
              <div>
                <div className="tl-agent-name">{agent.name}</div>
                <div className="mono tl-agent-role">{agent.role}</div>
              </div>
            </div>
            <div className="tl-track">
              {startAt != null && (
                <div className={'tl-bar ' + (isActive ? 'tl-bar-active' : '')}
                  style={{
                    left: `${(startAt/scale)*100}%`,
                    width: `${((endAt ?? (startAt+300))-startAt)/scale*100}%`,
                  }}>
                  <span className="tl-bar-msg mono">{st.message}</span>
                </div>
              )}
              {st.events.filter(e => e.status === 'running').map((e, ix) => (
                <div key={ix} className="tl-tick mono" style={{left: `${(e.at/scale)*100}%`}} title={e.message}></div>
              ))}
            </div>
            <div className="tl-meta mono">
              {endAt ? fmtTime(endAt - startAt) : (isActive ? '...' : '—')}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AgentTracePanel({ events, running, scenario, traceStyle, totalDuration }) {
  const completedCount = window.AGENTS.filter(a => AgentStatus(events, a.key).status === 'completed').length;
  const pct = running ? Math.min(95, (completedCount / 4) * 100) : (events.length ? 100 : 0);
  const supervisorLast = [...events].reverse().find(e => e.agent === 'supervisor');

  return (
    <section className="panel trace-panel">
      <div className="panel-head">
        <div className="panel-title">
          <span className="panel-ix mono">02</span>
          <h2>Agent trace</h2>
          <span className="mono subhead">4-agent CrewAI pipeline · GLM Supervisor</span>
        </div>
        <div style={{display:'flex', alignItems:'center', gap:8}}>
          {running && <span className="live-dot"><span className="live-dot-inner"></span>live</span>}
          {!running && events.length > 0 && <span className="badge badge-accent">resolved · {fmtTime(totalDuration || 0)}</span>}
          {!running && events.length === 0 && <span className="badge">idle</span>}
        </div>
      </div>

      <div className="trace-progress">
        <div className="trace-progress-bar" style={{width: pct + '%'}}></div>
      </div>

      {supervisorLast && (
        <div className="supervisor-line mono">
          <span className="sup-tag">SUPERVISOR</span>
          <span>{supervisorLast.message}</span>
        </div>
      )}

      {events.length === 0 && !running && (
        <div className="trace-empty">
          <EmptyIllustration />
          <div className="empty-title">Pipeline idle</div>
          <div className="empty-sub">Submit a complaint or pick a scenario to watch all 4 agents fire in sequence.</div>
        </div>
      )}

      {(events.length > 0 || running) && (
        <>
          {traceStyle === 'cards'    && <TraceCards events={events} />}
          {traceStyle === 'timeline' && <TraceTimeline events={events} running={running} />}
          {traceStyle === 'stepper'  && <TraceStepper events={events} running={running} />}
        </>
      )}
    </section>
  );
}

function EmptyIllustration() {
  return (
    <svg width="120" height="90" viewBox="0 0 120 90" fill="none" aria-hidden="true" style={{opacity:0.9}}>
      <rect x="10" y="18" width="100" height="54" rx="10" stroke="var(--border-strong)" strokeWidth="1.2" fill="var(--bg-subtle)"/>
      {[0,1,2,3].map(i => (
        <g key={i}>
          <circle cx={24 + i*24} cy="45" r="5.5" fill="var(--bg-elev)" stroke="var(--border-strong)" strokeWidth="1.2"/>
          {i < 3 && <line x1={29.5 + i*24} y1="45" x2={42.5 + i*24} y2="45" stroke="var(--border-strong)" strokeWidth="1.2" strokeDasharray="2 2"/>}
        </g>
      ))}
      <circle cx="24" cy="45" r="2" fill="var(--accent)" opacity="0.5"/>
    </svg>
  );
}

Object.assign(window, { AgentTracePanel });
