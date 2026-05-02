// IntegrationDemo: frontend-only mobile chat integration prototype.

const INTEGRATION_DEMOS = {
  lazada: {
    label: 'Lazada',
    accent: '#0F146D',
    accent2: '#FF6801',
    customer: 'Aina M.',
    initials: 'AM',
    order: 'LZ-20413879',
    product: 'Baju Kurung Moden',
    messages: [
      { id: 'lz-1', from: 'customer', name: 'Aina M.', time: '14:32', text: "Hi, my order hasn't arrived. It's been 2 weeks already. Tracking shows stuck at sorting center since 18 April." },
      { id: 'lz-2', from: 'customer', name: 'Aina M.', time: '14:32', text: "Order #LZ-20413879. I need a refund if you can't deliver by this week." },
      { id: 'lz-3', from: 'system', time: '14:32', text: 'Komplain.AI is analyzing this complaint...' },
      { id: 'lz-4', from: 'repeat-alert', time: '14:32', count: 2, text: 'Aina M. has filed 2 complaints in the last 30 days. Priority escalated.' },
      {
        id: 'lz-5',
        from: 'ai-suggestion',
        time: '14:33',
        confidence: 0.94,
        policy: 'Refund Policy 3.2',
        action: 'REFUND',
        text: "Hi Aina! I'm sorry about the delay with your order. I've checked the tracking and can confirm it has been stuck at the sorting center for 14 days, which exceeds our delivery promise.\n\nI've initiated a full refund of RM89.00 to your original payment method. You should see it within 3-5 business days.\n\nAgain, I apologize for the inconvenience. Is there anything else I can help with?",
      },
      {
        id: 'lz-6',
        from: 'agent',
        name: 'You',
        time: '14:33',
        text: "Hi Aina! I'm sorry about the delay with your order. I've checked the tracking and can confirm it has been stuck at the sorting center for 14 days, which exceeds our delivery promise.\n\nI've initiated a full refund of RM89.00 to your original payment method. You should see it within 3-5 business days.\n\nAgain, I apologize for the inconvenience. Is there anything else I can help with?",
        approved: true,
      },
      { id: 'lz-7', from: 'customer', name: 'Aina M.', time: '14:35', text: 'Ok thanks for the fast response!' },
    ],
  },
  shopee: {
    label: 'Shopee',
    accent: '#EE4D2D',
    accent2: '#EE4D2D',
    customer: 'Ahmad R.',
    initials: 'AR',
    order: 'SHP2041556',
    product: 'Baju Kurung Moden XL',
    messages: [
      { id: 'sh-1', from: 'customer', name: 'Ahmad R.', time: '09:15', text: 'Seller, saya terima barang rosak. Baju kurung koyak di bahagian lengan.' },
      { id: 'sh-2', from: 'customer', name: 'Ahmad R.', time: '09:15', text: 'Order #SHP2041556. Nak return dan refund boleh tak?', image: true },
      { id: 'sh-3', from: 'system', time: '09:15', text: 'Komplain.AI menganalisis aduan ini...' },
      {
        id: 'sh-4',
        from: 'ai-suggestion',
        time: '09:16',
        confidence: 0.91,
        policy: 'Return Policy 2.1 - Damaged Item',
        action: 'RETURN_REFUND',
        text: 'Hi Ahmad! Terima kasih kerana menghubungi kami. Saya minta maaf kerana barang yang diterima rosak.\n\nSaya telah menyemak gambar dan mengesahkan kerosakan. Sila ikut langkah berikut:\n1. Buka Shopee App > Orders > Return/Refund\n2. Pilih "Item damaged/defective"\n3. Upload gambar yang sama\n\nKami akan approve return request dalam masa 24 jam dan arrange pickup percuma.\n\nMaaf atas kesulitan ini!',
      },
      {
        id: 'sh-5',
        from: 'agent',
        name: 'You',
        time: '09:16',
        text: 'Hi Ahmad! Terima kasih kerana menghubungi kami. Saya minta maaf kerana barang yang diterima rosak.\n\nSaya telah menyemak gambar dan mengesahkan kerosakan. Sila ikut langkah berikut:\n1. Buka Shopee App > Orders > Return/Refund\n2. Pilih "Item damaged/defective"\n3. Upload gambar yang sama\n\nKami akan approve return request dalam masa 24 jam dan arrange pickup percuma.\n\nMaaf atas kesulitan ini!',
        approved: true,
      },
      { id: 'sh-6', from: 'customer', name: 'Ahmad R.', time: '09:18', text: 'Baik terima kasih seller! Dah submit.' },
    ],
  },
};

function IntegrationLogo({ platform }) {
  if (platform === 'shopee') {
    return (
      <svg viewBox="0 0 64 64" aria-hidden="true">
        <rect width="64" height="64" rx="12" fill="#EE4D2D" />
        <path d="M16 27c0-2 1-3 3-3h26c2 0 3 1 3 3l-2.5 22c-.3 2-1.5 3-3 3H21.5c-1.5 0-2.7-1-3-3L16 27z" fill="white" />
        <path d="M24 24v-4a8 8 0 0 1 16 0v4" stroke="white" strokeWidth="4" fill="none" strokeLinecap="round" />
        <text x="32" y="44" textAnchor="middle" fill="#EE4D2D" fontSize="22" fontWeight="800" fontFamily="Arial, sans-serif">S</text>
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <defs>
        <linearGradient id="integrationLazadaBg" x1="0" y1="0" x2="64" y2="64">
          <stop offset="0%" stopColor="#1A237E" />
          <stop offset="100%" stopColor="#283593" />
        </linearGradient>
        <linearGradient id="integrationLazadaLeft" x1="18" y1="20" x2="32" y2="48">
          <stop offset="0%" stopColor="#FF9800" />
          <stop offset="100%" stopColor="#FF6D00" />
        </linearGradient>
        <linearGradient id="integrationLazadaRight" x1="32" y1="20" x2="46" y2="48">
          <stop offset="0%" stopColor="#FF4081" />
          <stop offset="100%" stopColor="#E91E63" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="12" fill="url(#integrationLazadaBg)" />
      <path d="M14 28l18 18V32L22 22l-8 6z" fill="url(#integrationLazadaLeft)" />
      <path d="M50 28L32 46V32l10-10 8 6z" fill="url(#integrationLazadaRight)" />
    </svg>
  );
}

function PhoneStatusBar({ config }) {
  return (
    <div className="integration-statusbar" style={{ background: config.accent }}>
      <span className="integration-status-time mono">9:41</span>
      <span className="integration-island" aria-hidden="true"></span>
      <span className="integration-status-icons" aria-hidden="true">
        <svg viewBox="0 0 18 12"><rect x="1" y="8" width="3" height="4" rx="1" fill="currentColor" /><rect x="6" y="5" width="3" height="7" rx="1" fill="currentColor" /><rect x="11" y="2" width="3" height="10" rx="1" fill="currentColor" /></svg>
        <svg viewBox="0 0 22 12"><rect x="1" y="1" width="17" height="10" rx="3" fill="none" stroke="currentColor" strokeWidth="1.5" /><rect x="19" y="4" width="2" height="4" rx="1" fill="currentColor" /><rect x="3" y="3" width="13" height="6" rx="2" fill="currentColor" /></svg>
      </span>
    </div>
  );
}

function ChatHeader({ platform, config }) {
  return (
    <div className="integration-chat-header" style={{ background: config.accent }}>
      <button className="integration-header-back" type="button" aria-label="Back in chat">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 18l-6-6 6-6" /></svg>
      </button>
      <div className="integration-avatar" style={{ background: config.accent2 }}>{config.initials}</div>
      <div className="integration-chat-title">
        <strong>{config.customer}</strong>
        <span>Order #{config.order} - {config.product}</span>
      </div>
      <span className="integration-platform-mark"><IntegrationLogo platform={platform} /></span>
    </div>
  );
}

function CustomerMessage({ msg, config }) {
  return (
    <div className="integration-msg-row integration-msg-customer">
      <div className="integration-mini-avatar" style={{ background: config.accent2 }}>{msg.name.charAt(0)}</div>
      <div>
        <div className="integration-bubble integration-bubble-customer">
          {msg.text}
          {msg.image && (
            <div className="integration-image-placeholder">
              <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><path d="m21 15-5-5L5 21" /></svg>
              <span>Photo attached</span>
            </div>
          )}
        </div>
        <div className="integration-time">{msg.time}</div>
      </div>
    </div>
  );
}

function AgentMessage({ msg, config }) {
  return (
    <div className="integration-msg-row integration-msg-agent">
      <div className="integration-bubble integration-bubble-agent" style={{ borderColor: config.accent }}>
        {msg.text}
      </div>
      <div className="integration-time integration-time-agent">
        {msg.time}
        {msg.approved && <span>Sent</span>}
      </div>
    </div>
  );
}

function SystemMessage({ msg }) {
  return (
    <div className="integration-system">
      <span className="integration-dot" aria-hidden="true"></span>
      {msg.text}
    </div>
  );
}

function RepeatAlert({ msg }) {
  return (
    <div className="integration-repeat-alert">
      <div className="integration-alert-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /></svg>
      </div>
      <div>
        <div className="integration-alert-title">Repeat customer alert <span>{msg.count} complaints</span></div>
        <p>{msg.text}</p>
      </div>
    </div>
  );
}

function AISuggestion({ msg, config, approved }) {
  return (
    <div className="integration-ai-card" style={{ borderColor: config.accent }}>
      <div className="integration-ai-head">
        <span className="integration-ai-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" /></svg>
        </span>
        <strong>Komplain.AI Suggestion</strong>
        <span className="integration-confidence mono">{Math.round(msg.confidence * 100)}% conf</span>
      </div>
      <div className="integration-policy-row">
        <span>{msg.policy}</span>
        <span>Action: {msg.action}</span>
      </div>
      <div className="integration-suggestion-text">{msg.text}</div>
      {approved ? (
        <div className="integration-approved">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5" /></svg>
          Approved and sent to customer
        </div>
      ) : (
        <div className="integration-review-state">
          <span className="integration-dot" aria-hidden="true"></span>
          Waiting for seller approval
        </div>
      )}
    </div>
  );
}

function SellerReplyComposer({ config, suggestion, onSend }) {
  const [editing, setEditing] = React.useState(false);
  const [draft, setDraft] = React.useState(suggestion?.text || '');

  React.useEffect(() => {
    setDraft(suggestion?.text || '');
    setEditing(false);
  }, [suggestion?.id]);

  const sendReply = () => {
    if (!draft.trim()) return;
    onSend(draft.trim());
  };

  return (
    <div className="integration-seller-composer">
      <div className="integration-composer-head">
        <span className="integration-input-label mono">Seller review</span>
        <span className="integration-composer-policy">{suggestion?.action || 'ACTION'}</span>
      </div>
      {editing ? (
        <textarea
          className="integration-composer-edit"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          aria-label="Edit seller reply before sending"
        />
      ) : (
        <div className="integration-composer-preview">{draft}</div>
      )}
      <div className="integration-composer-actions">
        {editing ? (
          <>
            <button className="integration-mini-btn integration-send" style={{ background: config.accent }} type="button" onClick={sendReply}>Send edited reply</button>
            <button className="integration-mini-btn" type="button" onClick={() => { setDraft(suggestion?.text || ''); setEditing(false); }}>Reset</button>
          </>
        ) : (
          <>
            <button className="integration-mini-btn integration-send" style={{ background: config.accent }} type="button" onClick={sendReply}>Send reply</button>
            <button className="integration-mini-btn" type="button" onClick={() => setEditing(true)}>Edit reply</button>
          </>
        )}
      </div>
    </div>
  );
}

function ChatInput({ config, nextMsg, finished, waitingApproval, suggestion, onSend, onApprove }) {
  if (finished) {
    return <div className="integration-chat-input integration-ended">Conversation ended</div>;
  }

  if (waitingApproval) {
    return <SellerReplyComposer config={config} suggestion={suggestion} onSend={onApprove} />;
  }

  if (!nextMsg) {
    return (
      <div className="integration-chat-input">
        <div className="integration-waiting">Waiting...</div>
      </div>
    );
  }

  const preview = nextMsg.text.length > 58 ? `${nextMsg.text.slice(0, 58)}...` : nextMsg.text;

  return (
    <div className="integration-chat-input">
      <span className="integration-input-label mono">{nextMsg.from === 'customer' ? 'Customer will say' : 'Tap to send'}</span>
      <button className="integration-input-button" type="button" onClick={onSend}>
        <span style={{ borderColor: config.accent, color: config.accent }}>{preview}</span>
        <b style={{ background: config.accent }} aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M2.01 21 23 12 2.01 3 2 10l15 2-15 2z" /></svg>
        </b>
      </button>
    </div>
  );
}

function IntegrationChat({ platform, replayKey, onReplay }) {
  const config = INTEGRATION_DEMOS[platform];
  const conversation = config.messages;
  const [messages, setMessages] = React.useState([]);
  const [cursor, setCursor] = React.useState(0);
  const [waiting, setWaiting] = React.useState(false);
  const [waitingApproval, setWaitingApproval] = React.useState(false);
  const [approved, setApproved] = React.useState(false);
  const [activeSuggestion, setActiveSuggestion] = React.useState(null);
  const scrollRef = React.useRef(null);
  const timerRef = React.useRef(null);

  React.useEffect(() => {
    setMessages([]);
    setCursor(0);
    setWaiting(false);
    setWaitingApproval(false);
    setApproved(false);
    setActiveSuggestion(null);
    clearTimeout(timerRef.current);
  }, [platform, replayKey]);

  React.useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, waiting, waitingApproval]);

  React.useEffect(() => {
    if (!waiting) return undefined;
    if (cursor >= conversation.length) {
      setWaiting(false);
      return undefined;
    }

    const next = conversation[cursor];
    if (next.from === 'customer') {
      setWaiting(false);
      return undefined;
    }
    if (next.from === 'agent') {
      setWaiting(false);
      setWaitingApproval(true);
      return undefined;
    }

    const delay = next.from === 'system' ? 650 : next.from === 'repeat-alert' ? 900 : 1150;
    timerRef.current = setTimeout(() => {
      if (next.from === 'ai-suggestion') setActiveSuggestion(next);
      setMessages((prev) => [...prev, next]);
      setCursor((value) => value + 1);
    }, delay);

    return () => clearTimeout(timerRef.current);
  }, [waiting, cursor, conversation]);

  const handleSend = () => {
    if (waiting || waitingApproval || cursor >= conversation.length) return;
    setMessages((prev) => [...prev, conversation[cursor]]);
    setCursor((value) => value + 1);
    setWaiting(true);
  };

  const handleApprove = (replyText) => {
    setApproved(true);
    if (!waitingApproval || cursor >= conversation.length || conversation[cursor].from !== 'agent') return;
    timerRef.current = setTimeout(() => {
      const agentMsg = replyText ? { ...conversation[cursor], text: replyText } : conversation[cursor];
      setMessages((prev) => [...prev, agentMsg]);
      setCursor((value) => value + 1);
      setWaitingApproval(false);
      setActiveSuggestion(null);
      setWaiting(true);
    }, 400);
  };

  const finished = cursor >= conversation.length && !waiting && !waitingApproval;
  const nextMsg = cursor < conversation.length && !waiting && !waitingApproval ? conversation[cursor] : null;
  const showTyping = waiting && cursor < conversation.length && conversation[cursor].from !== 'customer';

  return (
    <div className="integration-chat">
      <ChatHeader platform={platform} config={config} />
      <div className="integration-thread" ref={scrollRef}>
        <div className="integration-date-pill">Today</div>
        {messages.map((msg) => {
          if (msg.from === 'customer') return <CustomerMessage key={msg.id} msg={msg} config={config} />;
          if (msg.from === 'agent') return <AgentMessage key={msg.id} msg={msg} config={config} />;
          if (msg.from === 'system') return <SystemMessage key={msg.id} msg={msg} />;
          if (msg.from === 'repeat-alert') return <RepeatAlert key={msg.id} msg={msg} />;
          if (msg.from === 'ai-suggestion') return <AISuggestion key={msg.id} msg={msg} config={config} approved={approved} />;
          return null;
        })}
        {showTyping && (
          <div className="integration-typing" aria-label="Komplain.AI typing">
            <span></span><span></span><span></span>
          </div>
        )}
        {waitingApproval && <div className="integration-approval-hint">Review the draft below, then send or edit it.</div>}
        {finished && (
          <div className="integration-finished">
            <span>Complaint resolved successfully</span>
            <button className="integration-mini-btn integration-send" style={{ background: config.accent }} type="button" onClick={onReplay}>Replay demo</button>
          </div>
        )}
      </div>
      <ChatInput
        config={config}
        nextMsg={nextMsg}
        finished={finished}
        waitingApproval={waitingApproval}
        suggestion={activeSuggestion}
        onSend={handleSend}
        onApprove={handleApprove}
      />
    </div>
  );
}

function IntegrationDemo({ onBack }) {
  const [platform, setPlatform] = React.useState('lazada');
  const [replayKey, setReplayKey] = React.useState(0);
  const config = INTEGRATION_DEMOS[platform];

  const switchPlatform = (nextPlatform) => {
    setPlatform(nextPlatform);
    setReplayKey((value) => value + 1);
  };

  return (
    <main className="integration-page">
      <div className="integration-shell">
        <div className="integration-nav">
          <button className="btn btn-secondary" type="button" onClick={onBack}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M15 18l-6-6 6-6" />
            </svg>
            Back to Dashboard
          </button>
        </div>

        <header className="integration-hero">
          <div className="command-kicker mono">
            <span className="command-pulse" aria-hidden="true"></span>
            Integration prototype
          </div>
          <h1>Customer service chat integration</h1>
          <p>Watch Komplain.AI analyze marketplace complaints, flag repeat customers, and draft policy-backed replies inside Lazada and Shopee support workflows.</p>
        </header>

        <div className="integration-tabs" role="tablist" aria-label="Marketplace demos">
          {Object.entries(INTEGRATION_DEMOS).map(([key, item]) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={platform === key}
              className={platform === key ? 'integration-tab integration-tab-active' : 'integration-tab'}
              style={platform === key ? { background: item.accent, borderColor: item.accent } : null}
              onClick={() => switchPlatform(key)}
            >
              <span><IntegrationLogo platform={key} /></span>
              {item.label}
            </button>
          ))}
        </div>

        <section className="integration-stage" aria-label={`${config.label} chat demo`}>
          <div className="integration-phone" style={{ '--integration-accent': config.accent }}>
            <PhoneStatusBar config={config} />
            <IntegrationChat platform={platform} replayKey={replayKey} onReplay={() => setReplayKey((value) => value + 1)} />
            <span className="integration-home" aria-hidden="true"></span>
          </div>
        </section>

        <div className="integration-callouts" aria-label="Integration strengths">
          <div><strong>Real-time analysis</strong><span>Complaint intent, order context, and risk cues appear after the customer message.</span></div>
          <div><strong>Policy-backed replies</strong><span>Suggestions include confidence, policy reference, and recommended action.</span></div>
          <div><strong>Agent control</strong><span>Support teams can approve instantly or edit before the response is sent.</span></div>
        </div>
      </div>
    </main>
  );
}

Object.assign(window, { IntegrationDemo });
