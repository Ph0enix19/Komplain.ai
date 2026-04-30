// CaseLog: recent case table, export, and detail modal

function CaseLog({ cases, onOpen, activeId }) {
  const [filter, setFilter] = React.useState('all');
  const [query, setQuery] = React.useState('');
  const filteredCases = cases.filter((caseItem) => {
    const matchesFilter = filter === 'all' || caseItem.status === filter;
    const haystack = `${caseItem.displayId || caseItem.id} ${caseItem.preview} ${caseItem.order} ${caseItem.lang} ${caseItem.resolution} ${caseItem.status}`.toLowerCase();
    return matchesFilter && haystack.includes(query.toLowerCase().trim());
  });

  const exportCases = () => {
    const columns = ['case_id', 'complaint', 'order', 'language', 'resolution', 'confidence', 'status', 'updated'];
    const escapeCell = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`;
    const rows = filteredCases.map((caseItem) => [
      caseItem.displayId || caseItem.id,
      caseItem.preview,
      caseItem.order,
      caseItem.lang,
      caseItem.resolution,
      Math.round(caseItem.confidence * 100) + '%',
      caseItem.status,
      caseItem.timestamp,
    ].map(escapeCell).join(','));
    const csv = [columns.join(','), ...rows].join('\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'komplain-cases.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="panel case-log" aria-labelledby="case-log-title">
      <div className="panel-head">
        <div className="panel-title">
          <span className="panel-ix mono">04</span>
          <h2 id="case-log-title">Case log</h2>
          <span className="mono subhead">{filteredCases.length} cases - last 24 h</span>
        </div>
        <div className="case-toolbar">
          <label className="case-search">
            <span className="sr-only">Search cases</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search cases"
            />
          </label>
          <div className="seg seg-sm" role="group" aria-label="Filter cases">
            <button className={'seg-btn ' + (filter === 'all' ? 'seg-active' : '')} type="button" aria-pressed={filter === 'all'} onClick={() => setFilter('all')}>All</button>
            <button className={'seg-btn ' + (filter === 'resolved' ? 'seg-active' : '')} type="button" aria-pressed={filter === 'resolved'} onClick={() => setFilter('resolved')}>Resolved</button>
            <button className={'seg-btn ' + (filter === 'review' ? 'seg-active' : '')} type="button" aria-pressed={filter === 'review'} onClick={() => setFilter('review')}>Review</button>
            <button className={'seg-btn ' + (filter === 'pending' ? 'seg-active' : '')} type="button" aria-pressed={filter === 'pending'} onClick={() => setFilter('pending')}>Pending</button>
          </div>
          <button className="btn btn-ghost btn-sm" type="button" onClick={exportCases} disabled={!filteredCases.length}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
            </svg>
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
          <div className="case-date">Updated</div>
        </div>

        {filteredCases.length === 0 && (
          <div className="trace-empty">
            <EmptyCaseIcon />
            <div className="empty-title">No cases match this view</div>
            <div className="empty-sub">Adjust search or switch filters to bring cases back into view.</div>
          </div>
        )}

        {filteredCases.map((caseItem) => {
          const meta = RESOLUTION_META[caseItem.resolution] || RESOLUTION_META.REFUND;
          const isActive = caseItem.id === activeId;

          return (
            <button key={caseItem.id} type="button" className={'case-row ' + (isActive ? 'case-row-active' : '')} onClick={() => onOpen(caseItem)}>
              <div className="mono case-id" title={caseItem.id}>
                {caseItem.displayId || caseItem.id}
                {isActive && <span className="case-live mono">live</span>}
              </div>
              <div className="case-preview">{caseItem.preview}</div>
              <div className="mono case-cell-muted">{caseItem.order}</div>
              <div className="mono case-cell-muted">{caseItem.lang}</div>
              <div><span className="res-pill mono" style={{ background: meta.bg, color: meta.fg }}>{caseItem.resolution}</span></div>
              <div className="mono"><ConfPill value={caseItem.confidence} /></div>
              <div><StatusPill status={caseItem.status} /></div>
              <div className="mono case-date">{caseItem.timestamp}</div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function EmptyCaseIcon() {
  return (
    <svg width="88" height="72" viewBox="0 0 88 72" fill="none" aria-hidden="true">
      <rect x="10" y="12" width="68" height="48" rx="8" fill="var(--surface)" stroke="var(--border-strong)" />
      <path d="M22 27h30M22 36h42M22 45h22" stroke="var(--border-strong)" strokeWidth="2" strokeLinecap="round" />
      <circle cx="64" cy="24" r="7" fill="var(--color-primary-soft)" stroke="var(--color-primary)" />
      <path d="M61 24h6" stroke="var(--color-primary)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function ConfPill({ value }) {
  const pct = Math.round(value * 100);
  const low = value < 0.8;

  return (
    <span className="conf-pill">
      <span className="conf-pill-bar">
        <span style={{ width: pct + '%', background: low ? 'var(--warning)' : 'var(--color-primary)' }}></span>
      </span>
      <span style={{ color: low ? 'var(--warning-fg)' : 'var(--text-muted)' }}>{pct}%</span>
    </span>
  );
}

function StatusPill({ status }) {
  const map = {
    resolved: { label: 'Resolved', cls: 'badge-accent' },
    review: { label: 'Review', cls: 'badge-warn' },
    pending: { label: 'Pending info', cls: 'badge-info' },
    processing: { label: 'Processing', cls: 'badge-info' },
  };
  const config = map[status] || { label: status, cls: '' };
  return <span className={'badge ' + config.cls}>{config.label}</span>;
}

function CaseDetailModal({ caseData, events, resolution, onClose, scenarioComplaint, orderData }) {
  if (!caseData) return null;

  const meta = RESOLUTION_META[caseData.resolution] || RESOLUTION_META.REFUND;
  const caseLabel = caseData.displayId || caseData.id;
  const order = orderData || window.MOCK_ORDERS[caseData.order];
  const orderView = order ? {
    id: order.id || order.order_id || '-',
    product: order.product_name || order.item || '-',
    orderDate: order.order_date || order.delivery_date || '-',
    courier: order.courier || '-',
    tracking: order.tracking || '-',
    status: order.delivery_status || order.status || '-',
    daysSince: order.days_since_order || '-',
    refundWindow: order.seller_policy_refund_days || '-',
  } : null;

  return (
    <div className="modal-scrim" onClick={onClose} role="presentation">
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="case-detail-title" onClick={(event) => event.stopPropagation()}>
        <header className="modal-head">
          <div>
            <div className="mono modal-kicker" title={caseData.id}>CASE - {caseLabel}</div>
            <h2 className="modal-title" id="case-detail-title">Complaint detail <span className="modal-title-sub">review view</span></h2>
          </div>
          <div className="modal-actions">
            <span className="res-pill mono" style={{ background: meta.bg, color: meta.fg, fontSize: 12, padding: '4px 10px' }}>{caseData.resolution}</span>
            <StatusPill status={caseData.status} />
            <button className="btn btn-ghost btn-icon" type="button" onClick={onClose} aria-label="Close case detail">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        </header>

        <div className="modal-grid">
          <div className="modal-main">
            <section className="modal-section">
              <div className="section-label mono">COMPLAINT - RAW INPUT</div>
              <blockquote className="complaint-quote">
                {scenarioComplaint || 'My order ORD-2041 has not arrived after two weeks. Please help me get a refund.'}
              </blockquote>
              <div className="complaint-meta mono">
                <span>{caseData.lang}</span>
                <span>{caseData.timestamp}</span>
                <span>{caseData.order}</span>
              </div>
            </section>

            <section className="modal-section">
              <div className="section-label mono">AGENT TRACE - FULL</div>
              <div className="modal-trace">
                {window.AGENTS.map((agent, index) => {
                  const mine = events.filter((event) => event.agent === agent.key);
                  const last = mine[mine.length - 1];
                  const output = mine.find((event) => event.output)?.output;
                  const status = last?.status || 'completed';

                  return (
                    <div key={agent.key} className={'modal-trace-row status-' + status}>
                      <div className="modal-trace-head">
                        <span className="mono trace-time">0{index + 1}</span>
                        <StatusIcon status={status} />
                        <span className="modal-trace-name">{agent.name}</span>
                        <span className={'badge ' + (status === 'completed' ? 'badge-accent' : status === 'failed' ? 'badge-danger' : 'badge-info')}>{status}</span>
                      </div>
                      <div className="modal-trace-log">
                        {mine.map((event, eventIndex) => (
                          <div key={eventIndex} className="log-line mono">
                            <span className="log-time">{(event.at / 1000).toFixed(2)}s</span>
                            <span className={'log-dot status-' + event.status}></span>
                            <span className="log-msg">{event.message}</span>
                          </div>
                        ))}
                      </div>
                      {output && <pre className="modal-json mono">{JSON.stringify(output, null, 2)}</pre>}
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="modal-section">
              <div className="section-label mono">RESOLUTION - FINAL</div>
              {resolution && (
                <>
                  <div className="res-reason">
                    <p>{resolution.reason}</p>
                    <div className="res-policy mono">{resolution.policy}</div>
                  </div>
                  <div className="res-replies">
                    <ReplyBlock lang="EN" text={resolution.response_en} tone="friendly" />
                    <ReplyBlock lang="BM" text={resolution.response_bm} tone="friendly" primary />
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
                    <div className="t-meta mono">4 agents - GLM-5.1</div>
                  </div>
                </li>
                <li className={'timeline-item ' + (caseData.status === 'resolved' ? 'done' : 'active')}>
                  <span className="t-dot"></span>
                  <div>
                    <div className="t-title">{caseData.status === 'resolved' ? 'Resolution approved' : 'Awaiting review'}</div>
                    <div className="t-meta mono">{caseData.status === 'resolved' ? 'approved - EN + BM' : 'flagged - conf < 0.80'}</div>
                  </div>
                </li>
                <li className="timeline-item">
                  <span className="t-dot"></span>
                  <div>
                    <div className="t-title">Reply sent to customer</div>
                    <div className="t-meta mono">via email + WhatsApp</div>
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
                  <div><span className="kv-k">status</span><span style={{ color: 'var(--warning-fg)' }}>{orderView.status}</span></div>
                  <div><span className="kv-k">days_since</span><span>{orderView.daysSince}</span></div>
                  <div><span className="kv-k">refund_window</span><span>{orderView.refundWindow === '-' ? '-' : `${orderView.refundWindow}d`}</span></div>
                </div>
              </div>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { CaseLog, CaseDetailModal, StatusPill });
