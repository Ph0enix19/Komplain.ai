// CaseLog — bottom strip + CaseDetail modal

function CaseLog({ cases, onOpen, activeId }) {
  const [filter, setFilter] = React.useState('all');
  const filteredCases = cases.filter((c) => {
    if (filter === 'all') return true;
    return c.status === filter;
  });

  return (
    <section className="panel case-log">
      <div className="panel-head">
        <div className="panel-title">
          <span className="panel-ix mono">04</span>
          <h2>Case log</h2>
          <span className="mono subhead">{filteredCases.length} cases · last 24 h</span>
        </div>
        <div style={{display:'flex', gap:8, alignItems:'center'}}>
          <div className="seg seg-sm">
            <button className={'seg-btn ' + (filter === 'all' ? 'seg-active' : '')} type="button" onClick={() => setFilter('all')}>All</button>
            <button className={'seg-btn ' + (filter === 'resolved' ? 'seg-active' : '')} type="button" onClick={() => setFilter('resolved')}>Resolved</button>
            <button className={'seg-btn ' + (filter === 'review' ? 'seg-active' : '')} type="button" onClick={() => setFilter('review')}>Review</button>
            <button className={'seg-btn ' + (filter === 'pending' ? 'seg-active' : '')} type="button" onClick={() => setFilter('pending')}>Pending</button>
          </div>
          <button className="btn btn-ghost btn-sm" type="button">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
            Export
          </button>
        </div>
      </div>
      <div className="case-table">
        <div className="case-row case-head mono">
          <div>Case ID</div>
          <div>Complaint</div>
          <div>Order</div>
          <div>Lang</div>
          <div>Resolution</div>
          <div>Conf.</div>
          <div>Status</div>
          <div style={{textAlign:'right'}}>Updated</div>
        </div>
        {filteredCases.map(c => {
          const meta = RESOLUTION_META[c.resolution] || RESOLUTION_META.REFUND;
          const isActive = c.id === activeId;
          return (
            <button key={c.id} type="button" className={'case-row ' + (isActive ? 'case-row-active' : '')} onClick={() => onOpen(c)}>
              <div className="mono case-id" title={c.id}>{c.displayId || c.id}{isActive && <span className="case-live mono">live</span>}</div>
              <div className="case-preview">{c.preview}</div>
              <div className="mono" style={{color:'var(--fg-muted)'}}>{c.order}</div>
              <div className="mono" style={{color:'var(--fg-muted)', fontSize:11}}>{c.lang}</div>
              <div><span className="res-pill mono" style={{background: meta.bg, color: meta.fg}}>{c.resolution}</span></div>
              <div className="mono conf-cell"><ConfPill value={c.confidence}/></div>
              <div><StatusPill status={c.status} /></div>
              <div className="mono" style={{textAlign:'right', color:'var(--fg-subtle)'}}>{c.timestamp}</div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function ConfPill({ value }) {
  const pct = Math.round(value * 100);
  const low = value < 0.8;
  return (
    <span className="conf-pill">
      <span className="conf-pill-bar">
        <span style={{width: pct + '%', background: low ? 'var(--warn)' : 'var(--accent)'}}></span>
      </span>
      <span style={{color: low ? 'var(--warn-fg)' : 'var(--fg-muted)'}}>{pct}%</span>
    </span>
  );
}

function StatusPill({ status }) {
  const map = {
    resolved: { label: 'Resolved', cls: 'badge-accent' },
    review:   { label: 'Review',   cls: 'badge-warn' },
    pending:  { label: 'Pending info', cls: 'badge-info' },
    processing: { label: 'Processing', cls: 'badge-info' },
  };
  const m = map[status] || { label: status, cls: '' };
  return <span className={'badge ' + m.cls}>{m.label}</span>;
}

// ---------------- Case Detail Modal ----------------

function CaseDetailModal({ caseData, events, resolution, onClose, scenarioComplaint, orderData }) {
  if (!caseData) return null;
  const meta = RESOLUTION_META[caseData.resolution] || RESOLUTION_META.REFUND;
  const caseLabel = caseData.displayId || caseData.id;
  const order = orderData || window.MOCK_ORDERS[caseData.order];
  const orderView = order ? {
    id: order.id || order.order_id || '—',
    product: order.product_name || order.item || '—',
    orderDate: order.order_date || order.delivery_date || '—',
    courier: order.courier || '—',
    tracking: order.tracking || '—',
    status: order.delivery_status || order.status || '—',
    daysSince: order.days_since_order || '—',
    refundWindow: order.seller_policy_refund_days || '—',
  } : null;

  return (
    <div className="modal-scrim" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <header className="modal-head">
          <div>
            <div className="mono" style={{color:'var(--fg-subtle)', fontSize:11}} title={caseData.id}>CASE · {caseLabel}</div>
            <h2 className="modal-title">Complaint detail <span style={{color:'var(--fg-muted)', fontWeight:400, fontSize:14}}>· debug view</span></h2>
          </div>
          <div style={{display:'flex', gap:8, alignItems:'center'}}>
            <span className="res-pill mono" style={{background: meta.bg, color: meta.fg, fontSize:12, padding:'4px 10px'}}>{caseData.resolution}</span>
            <StatusPill status={caseData.status} />
            <button className="btn btn-ghost" type="button" onClick={onClose} aria-label="Close">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
        </header>

        <div className="modal-grid">
          <div className="modal-main">
            <section className="modal-section">
              <div className="section-label mono">COMPLAINT · raw input</div>
              <blockquote className="complaint-quote">
                {scenarioComplaint || "Brader, barang saya tak sampai lagi la. Dah 2 minggu tracking still processing je. Mana pergi barang saya ni? Order ORD-2041. Kalau tak settle hari ni, I nak refund balik."}
              </blockquote>
              <div className="complaint-meta mono">
                <span>· {caseData.lang}</span>
                <span>· {caseData.timestamp}</span>
                <span>· {caseData.order}</span>
              </div>
            </section>

            <section className="modal-section">
              <div className="section-label mono">AGENT TRACE · full</div>
              <div className="modal-trace">
                {window.AGENTS.map((agent, i) => {
                  const mine = events.filter(e => e.agent === agent.key);
                  const last = mine[mine.length-1];
                  const out = mine.find(e => e.output)?.output;
                  const status = last?.status || 'completed';
                  return (
                    <div key={agent.key} className={'modal-trace-row status-' + status}>
                      <div className="modal-trace-head">
                        <span className="mono" style={{color:'var(--fg-subtle)', fontSize:11}}>0{i+1}</span>
                        <StatusIcon status={status} />
                        <span className="modal-trace-name">{agent.name}</span>
                        <span className={'badge ' + (status === 'completed' ? 'badge-accent' : status === 'failed' ? 'badge-danger' : 'badge-info')}>{status}</span>
                      </div>
                      <div className="modal-trace-log">
                        {mine.map((e, ix) => (
                          <div key={ix} className="log-line mono">
                            <span className="log-time">{(e.at/1000).toFixed(2)}s</span>
                            <span className={'log-dot status-' + e.status}></span>
                            <span className="log-msg">{e.message}</span>
                          </div>
                        ))}
                      </div>
                      {out && (
                        <pre className="modal-json mono">{JSON.stringify(out, null, 2)}</pre>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="modal-section">
              <div className="section-label mono">RESOLUTION · final</div>
              {resolution && (
                <>
                  <div className="res-reason">
                    <p style={{marginTop:0}}>{resolution.reason}</p>
                    <div className="res-policy mono">{resolution.policy}</div>
                  </div>
                  <div className="res-replies" style={{marginTop:12}}>
                    <ReplyBlock lang="EN" flag="🇬🇧" text={resolution.response_en} tone="friendly" />
                    <ReplyBlock lang="BM" flag="🇲🇾" text={resolution.response_bm} tone="friendly" primary />
                  </div>
                </>
              )}
            </section>
          </div>

          <aside className="modal-side">
            <div className="side-block">
              <div className="section-label mono">STATUS TIMELINE</div>
              <ol className="timeline">
                <li className="timeline-item done">
                  <span className="t-dot"></span>
                  <div>
                    <div className="t-title">Complaint received</div>
                    <div className="t-meta mono">{caseData.timestamp}</div>
                  </div>
                </li>
                <li className="timeline-item done">
                  <span className="t-dot"></span>
                  <div>
                    <div className="t-title">Pipeline completed</div>
                    <div className="t-meta mono">4 agents · 5.34s</div>
                  </div>
                </li>
                <li className={'timeline-item ' + (caseData.status === 'resolved' ? 'done' : 'active')}>
                  <span className="t-dot"></span>
                  <div>
                    <div className="t-title">{caseData.status === 'resolved' ? 'Seller approved' : 'Awaiting seller review'}</div>
                    <div className="t-meta mono">{caseData.status === 'resolved' ? 'auto-sent · EN + BM' : 'flagged · conf < 0.80'}</div>
                  </div>
                </li>
                <li className="timeline-item">
                  <span className="t-dot"></span>
                  <div>
                    <div className="t-title">Reply sent to customer</div>
                    <div className="t-meta mono">via email + wa</div>
                  </div>
                </li>
              </ol>
            </div>

            {orderView && (
              <div className="side-block">
                <div className="section-label mono">ORDER CONTEXT</div>
                <div className="kv-grid mono">
                  <div><span className="kv-k">id</span><span>{orderView.id}</span></div>
                  <div><span className="kv-k">product</span><span>{orderView.product}</span></div>
                  <div><span className="kv-k">order_date</span><span>{orderView.orderDate}</span></div>
                  <div><span className="kv-k">courier</span><span>{orderView.courier}</span></div>
                  <div><span className="kv-k">tracking</span><span>{orderView.tracking}</span></div>
                  <div><span className="kv-k">status</span><span style={{color:'var(--warn-fg)'}}>{orderView.status}</span></div>
                  <div><span className="kv-k">days_since</span><span>{orderView.daysSince}</span></div>
                  <div><span className="kv-k">refund_window</span><span>{orderView.refundWindow === '—' ? '—' : `${orderView.refundWindow}d`}</span></div>
                </div>
              </div>
            )}

            <div className="side-block">
              <div className="section-label mono">LANGSMITH TRACE</div>
              <div className="ls-trace mono">
                <div className="ls-row"><span>trace_id</span><span>trc_2047ab</span></div>
                <div className="ls-row"><span>model</span><span>glm-4-{caseData.id.slice(-4)}</span></div>
                <div className="ls-row"><span>prompt_tokens</span><span>2,481</span></div>
                <div className="ls-row"><span>completion_tokens</span><span>1,092</span></div>
                <div className="ls-row"><span>cost</span><span>$0.014</span></div>
              </div>
              <a className="ls-link mono">open in LangSmith →</a>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { CaseLog, CaseDetailModal, StatusPill });
