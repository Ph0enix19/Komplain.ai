// ResolutionCard: decision, rationale, reply review, and approval actions

const RESOLUTION_META = {
  REFUND: { color: 'var(--info)', bg: 'var(--info-soft)', fg: 'var(--info-fg)', icon: 'refund', label: 'REFUND' },
  RESHIP: { color: 'var(--color-primary)', bg: 'var(--color-primary-soft)', fg: 'var(--color-primary-hover)', icon: 'reship', label: 'RESHIP' },
  ESCALATE: { color: 'var(--warning)', bg: 'var(--warning-soft)', fg: 'var(--warning-fg)', icon: 'escalate', label: 'ESCALATE' },
  DISMISS: { color: 'var(--text-muted)', bg: 'var(--color-secondary-soft)', fg: 'var(--text)', icon: 'dismiss', label: 'DISMISS' },
  CLARIFY: { color: 'var(--warning)', bg: 'var(--warning-soft)', fg: 'var(--warning-fg)', icon: 'clarify', label: 'CLARIFY' },
};

function ConfidenceMeter({ value }) {
  const pct = Math.round(value * 100);
  const low = value < 0.8;

  return (
    <div className="conf">
      <div className="conf-head">
        <span className="label">Confidence</span>
        <span className="mono conf-val" style={{ color: low ? 'var(--warning-fg)' : 'var(--color-primary-hover)' }}>{pct}%</span>
      </div>
      <div className="conf-track" aria-label={`Confidence ${pct}%`}>
        <div className="conf-fill" style={{ width: pct + '%', background: low ? 'var(--warning)' : 'var(--color-primary)' }}></div>
        <div className="conf-threshold" style={{ left: '80%' }} title="Human review threshold"></div>
      </div>
      <div className="conf-foot mono">
        <span>0.0</span>
        <span style={{ color: low ? 'var(--warning-fg)' : 'var(--text-subtle)' }}>review threshold 0.80</span>
        <span>1.0</span>
      </div>
    </div>
  );
}

function ResolutionCard({
  running,
  resolution,
  onApprove,
  tone,
  onOpenDetail,
  isEditing,
  draft,
  onDraftChange,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onCopyReply,
}) {
  if (!resolution && !running) {
    return (
      <aside className="panel resolution-panel" aria-labelledby="resolution-title">
        <div className="panel-head">
          <div className="panel-title">
            <span className="panel-ix mono">03</span>
            <h2 id="resolution-title">Resolution</h2>
            <span className="mono subhead">Decision and bilingual reply review</span>
          </div>
          <span className="badge">Awaiting</span>
        </div>
        <div className="res-empty">
          <ResIllustration />
          <div className="empty-title">No resolution yet</div>
          <div className="empty-sub">When the pipeline completes, the decision and bilingual reply appear here for review.</div>
        </div>
      </aside>
    );
  }

  if (running && !resolution) {
    return (
      <aside className="panel resolution-panel" aria-labelledby="resolution-title">
        <div className="panel-head">
          <div className="panel-title">
            <span className="panel-ix mono">03</span>
            <h2 id="resolution-title">Resolution</h2>
            <span className="mono subhead">Drafting customer response</span>
          </div>
          <span className="badge badge-info">Drafting</span>
        </div>
        <div className="res-skeleton" aria-label="Loading resolution">
          <div className="sk-line" style={{ width: '42%', height: 32, marginBottom: 16 }}></div>
          <div className="sk-line" style={{ width: '100%', height: 12, marginBottom: 8 }}></div>
          <div className="sk-line" style={{ width: '78%', height: 12, marginBottom: 20 }}></div>
          <div className="sk-line" style={{ width: '100%', height: 88, marginBottom: 12 }}></div>
          <div className="sk-line" style={{ width: '100%', height: 88 }}></div>
        </div>
      </aside>
    );
  }

  const meta = RESOLUTION_META[resolution.type] || RESOLUTION_META.REFUND;
  const hasAmount = resolution.amount && resolution.amount !== '-';

  return (
    <aside className="panel resolution-panel" aria-labelledby="resolution-title">
      <div className="panel-head">
        <div className="panel-title">
          <span className="panel-ix mono">03</span>
          <h2 id="resolution-title">Resolution</h2>
          <span className="mono subhead">Supervisor-ready outcome</span>
        </div>
        <button className="btn btn-ghost btn-sm" type="button" onClick={onOpenDetail}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M15 3h6v6M14 10l7-7M9 21H3v-6M10 14l-7 7" />
          </svg>
          Detail
        </button>
      </div>

      <div className="res-decision">
        <div className="res-badge" style={{ background: meta.bg, color: meta.fg }}>
          <ResolutionIcon name={meta.icon} />
          <span className="mono">{meta.label}</span>
        </div>
        {hasAmount && <div className="res-amount mono">{resolution.amount}</div>}
      </div>

      <ConfidenceMeter value={resolution.confidence} />

      {resolution.requires_review && (
        <div className="review-flag" role="alert">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <path d="M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          </svg>
          <div>
            <div className="review-flag-title">Requires human review</div>
            <div className="review-flag-sub">Confidence is below the 0.80 threshold. Approve or edit before sending.</div>
          </div>
        </div>
      )}

      <div className="res-reason">
        <span className="label">Reasoning</span>
        <p>{resolution.reason}</p>
        <div className="res-policy mono">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <path d="M14 2v6h6" />
          </svg>
          {resolution.policy}
        </div>
      </div>

      <div className="res-replies">
        <ReplyBlock
          lang="EN"
          text={isEditing ? draft.response_en : resolution.response_en}
          tone={tone}
          editable={isEditing}
          onChange={(value) => onDraftChange({ ...draft, response_en: value })}
          onCopy={onCopyReply}
        />
        <ReplyBlock
          lang="BM"
          text={isEditing ? draft.response_bm : resolution.response_bm}
          tone={tone}
          primary
          editable={isEditing}
          onChange={(value) => onDraftChange({ ...draft, response_bm: value })}
          onCopy={onCopyReply}
        />
      </div>

      <div className="res-actions">
        {!isEditing && (
          <button className="btn btn-ghost" type="button" onClick={onStartEdit}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            Edit replies
          </button>
        )}
        {isEditing && (
          <button className="btn btn-ghost" type="button" onClick={onCancelEdit}>Cancel</button>
        )}
        {isEditing && (
          <button className="btn btn-primary" type="button" onClick={onSaveEdit}>Save draft</button>
        )}
        {!isEditing && (
          <button className="btn btn-primary" type="button" onClick={onApprove}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true">
              <path d="M5 13l4 4L19 7" />
            </svg>
            Approve and close case
          </button>
        )}
      </div>
    </aside>
  );
}

function ReplyBlock({ lang, text, tone, primary, editable, onChange, onCopy }) {
  const replyLabel = lang === 'EN' ? 'English reply' : 'Bahasa Malaysia reply';

  return (
    <div className={'reply ' + (primary ? 'reply-primary' : '')}>
      <div className="reply-head">
        <span className="reply-flag mono">{lang}</span>
        <span className="reply-lang mono">{replyLabel}</span>
        <span className="reply-meta mono">{text.length} chars - tone: {tone}</span>
        {onCopy && (
          <button className="reply-copy" type="button" title="Copy reply" aria-label={`Copy ${replyLabel}`} onClick={() => onCopy(text)}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <rect x="9" y="9" width="13" height="13" rx="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
          </button>
        )}
      </div>
      {editable ? (
        <textarea
          className="textarea reply-editor"
          rows={6}
          value={text}
          onChange={(event) => onChange(event.target.value)}
        />
      ) : (
        <pre className="reply-body">{text}</pre>
      )}
    </div>
  );
}

function ResolutionIcon({ name }) {
  const iconProps = { width: 14, height: 14, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true };
  if (name === 'refund') return <svg {...iconProps}><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 0 1 4-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 0 1-4 4H3" /></svg>;
  if (name === 'reship') return <svg {...iconProps}><rect x="1" y="7" width="15" height="10" rx="1" /><path d="M16 10h4l3 3v4h-7" /><circle cx="5.5" cy="19" r="2" /><circle cx="18.5" cy="19" r="2" /></svg>;
  if (name === 'escalate') return <svg {...iconProps}><path d="M12 2l10 18H2z" /><path d="M12 9v4M12 17h.01" /></svg>;
  if (name === 'dismiss') return <svg {...iconProps}><circle cx="12" cy="12" r="10" /><path d="M8 8l8 8M16 8l-8 8" /></svg>;
  if (name === 'clarify') return <svg {...iconProps}><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01" /></svg>;
  return null;
}

function ResIllustration() {
  return (
    <svg width="120" height="90" viewBox="0 0 120 90" fill="none" aria-hidden="true">
      <rect x="18" y="12" width="84" height="66" rx="10" stroke="var(--border-strong)" strokeWidth="1.2" fill="var(--surface-inset)" />
      <rect x="28" y="24" width="40" height="8" rx="3" fill="var(--border-strong)" opacity="0.6" />
      <rect x="28" y="38" width="64" height="4" rx="2" fill="var(--border)" />
      <rect x="28" y="46" width="48" height="4" rx="2" fill="var(--border)" />
      <rect x="28" y="58" width="30" height="12" rx="3" stroke="var(--color-primary)" strokeWidth="1.3" strokeDasharray="3 3" fill="none" />
    </svg>
  );
}

Object.assign(window, { ResolutionCard, RESOLUTION_META, ReplyBlock });
