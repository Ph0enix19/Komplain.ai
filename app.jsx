// Main App — wires everything

const { useState, useEffect, useRef } = React;

const API_BASE = 'http://127.0.0.1:8000/api';

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "light",
  "density": "comfortable",
  "tone": "friendly",
  "traceStyle": "stepper"
}/*EDITMODE-END*/;

function adjustTone(text, tone) {
  if (tone === 'formal') {
    return text.replace(/^Hi there,/, 'Dear Customer,').replace(/^Hi,/, 'Dear Customer,').replace(/— Komplain.ai Support/, 'Sincerely,\nCustomer Support');
  }
  if (tone === 'technical') {
    return text.replace(/^Hi there,\n\n/, '[AUTO-DRAFT · GLM-5.1]\n\n').replace(/^Hi,\n\n/, '[AUTO-DRAFT · GLM-5.1]\n\n');
  }
  return text;
}

function parseTimestamp(value) {
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? Date.now() : parsed;
}

function formatTimestamp(value) {
  const date = new Date(value);
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  const hh = String(date.getHours()).padStart(2, '0');
  const min = String(date.getMinutes()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd} ${hh}:${min}`;
}

function buildDisplayCaseId(rawId, fallback = 'CMP-LIVE') {
  if (!rawId) return fallback;
  if (rawId.startsWith('CMP-')) return rawId;
  const compact = rawId.replace(/[^a-zA-Z0-9]/g, '').slice(-6).toUpperCase();
  return `CMP-${compact || 'LIVE'}`;
}

function inferLanguage(text) {
  const lowered = text.toLowerCase();
  if (/\b(saya|barang|tak|lagi|nak|refund|pesanan|terima kasih)\b/.test(lowered) && /\b(order|tracking|refund|processing)\b/.test(lowered)) {
    return 'Manglish';
  }
  if (/\b(saya|barang|tak|lagi|nak|pesanan|terima kasih)\b/.test(lowered)) return 'BM';
  return 'EN';
}

function buildCaseStatus(record) {
  if (!record.context.order_found && !record.intake.order_id) return 'pending';
  return record.reasoning.requires_human_review ? 'review' : 'resolved';
}

function buildAmount(record) {
  const decision = record.reasoning.decision;
  const order = record.context.order_data;
  if (decision === 'REFUND' && order?.total && order?.currency) {
    return `${order.currency} ${Number(order.total).toFixed(2)}`;
  }
  if (decision === 'RESHIP') return '1 × replacement';
  return '—';
}

function buildPolicy(record) {
  if (!record.context.order_found && !record.intake.order_id) return 'Supervisor review · missing order ID';
  if (!record.context.order_found) return 'Supervisor review · order lookup failed';
  if (record.reasoning.decision === 'REFUND') return 'Order policy · refund path selected';
  if (record.reasoning.decision === 'RESHIP') return 'Order policy · replacement path selected';
  return 'Supervisor logic · manual review';
}

function buildResolution(record) {
  const needsClarification = !record.intake.order_id;
  const decision = needsClarification ? 'CLARIFY' : record.reasoning.decision;
  return {
    type: decision,
    confidence: record.reasoning.confidence,
    reason: record.reasoning.rationale,
    policy: buildPolicy(record),
    response_en: record.response.english,
    response_bm: record.response.bahasa_malaysia,
    amount: buildAmount(record),
    requires_review: record.reasoning.requires_human_review,
  };
}

function buildCaseFromRecord(record) {
  const resolution = buildResolution(record);
  return {
    id: record.id,
    displayId: buildDisplayCaseId(record.id),
    preview: record.complaint_text.slice(0, 72) + (record.complaint_text.length > 72 ? '…' : ''),
    resolution: resolution.type,
    confidence: record.reasoning.confidence,
    status: buildCaseStatus(record),
    timestamp: formatTimestamp(record.created_at),
    order: record.intake.order_id || '—',
    lang: inferLanguage(record.complaint_text),
    complaintId: record.id,
    source: 'api',
  };
}

function buildTimelineEvents(apiEvents) {
  const events = [];
  let cursor = 120;

  apiEvents.forEach((event) => {
    const isContextFailure = event.step === 'context' && event.payload?.order_found === false;
    events.push({
      at: cursor,
      agent: event.step,
      status: 'started',
      message: `${event.step[0].toUpperCase()}${event.step.slice(1)} agent started`,
    });
    cursor += 280;
    events.push({
      at: cursor,
      agent: event.step,
      status: isContextFailure ? 'failed' : 'running',
      message: event.message,
      output: isContextFailure ? event.payload : null,
    });
    cursor += 320;
    if (!isContextFailure) {
      events.push({
        at: cursor,
        agent: event.step,
        status: 'completed',
        message: event.message,
        output: event.payload,
      });
      cursor += 260;
    }
  });

  return events;
}

async function apiFetch(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }
  return response.json();
}

function App() {
  const [theme, setTheme] = useState(TWEAK_DEFAULTS.theme);
  const [density, setDensity] = useState(TWEAK_DEFAULTS.density);
  const [tone, setTone] = useState(TWEAK_DEFAULTS.tone);
  const [traceStyle, setTraceStyle] = useState(TWEAK_DEFAULTS.traceStyle);

  const [tweaksHostActive, setTweaksHostActive] = useState(false);
  const [tweaksUserOpen, setTweaksUserOpen] = useState(false);

  const [complaint, setComplaint] = useState(window.SCENARIOS[0].complaint);
  const [orderId, setOrderId] = useState(window.SCENARIOS[0].orderId);
  const [scenarioKey, setScenarioKey] = useState('manglish');

  const [events, setEvents] = useState([]);
  const [running, setRunning] = useState(false);
  const [resolution, setResolution] = useState(null);
  const [editingResolution, setEditingResolution] = useState(false);
  const [resolutionDraft, setResolutionDraft] = useState({ response_en: '', response_bm: '' });
  const [totalDuration, setTotalDuration] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const timers = useRef([]);

  const [cases, setCases] = useState([]);
  const [caseRecords, setCaseRecords] = useState({});
  const [caseEvents, setCaseEvents] = useState({});
  const [modalCase, setModalCase] = useState(null);
  const [activeCaseId, setActiveCaseId] = useState(null);
  const liveCaseId = useRef(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-density', density);
  }, [theme, density]);

  useEffect(() => {
    const onMsg = (e) => {
      if (!e.data || typeof e.data !== 'object') return;
      if (e.data.type === '__activate_edit_mode') { setTweaksHostActive(true); setTweaksUserOpen(true); }
      if (e.data.type === '__deactivate_edit_mode') { setTweaksHostActive(false); setTweaksUserOpen(false); }
    };
    window.addEventListener('message', onMsg);
    window.parent.postMessage({ type: '__edit_mode_available' }, '*');
    return () => window.removeEventListener('message', onMsg);
  }, []);

  const persist = (edits) => window.parent.postMessage({ type: '__edit_mode_set_keys', edits }, '*');
  const wrap = (setter, key) => (value) => { setter(value); persist({ [key]: value }); };

  useEffect(() => () => { timers.current.forEach(clearTimeout); }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadComplaints() {
      try {
        const records = await apiFetch('/complaints');
        if (cancelled) return;
        const mapped = [...records]
          .sort((a, b) => parseTimestamp(b.created_at) - parseTimestamp(a.created_at))
          .map(buildCaseFromRecord);
        const recordMap = records.reduce((acc, record) => {
          acc[record.id] = record;
          return acc;
        }, {});
        setCaseRecords(recordMap);
        setCases(mapped.slice(0, 5));
      } catch (error) {
        console.error(error);
        if (!cancelled) setErrorMessage('Backend not reachable. Make sure the API is running on port 8000.');
      }
    }

    loadComplaints();
    return () => { cancelled = true; };
  }, []);

  const scheduleTimeline = (timelineEvents, finalResolution, caseId) => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setEvents([]);
    setResolution(null);
    setEditingResolution(false);
    setResolutionDraft({ response_en: '', response_bm: '' });

    timelineEvents.forEach((event) => {
      const timer = setTimeout(() => {
        setEvents((prev) => [...prev, event]);
      }, event.at);
      timers.current.push(timer);
    });

    const finishAt = timelineEvents.length ? timelineEvents[timelineEvents.length - 1].at : 0;
    const resolutionTimer = setTimeout(() => {
      setResolution(finalResolution);
    }, Math.max(0, finishAt - 240));
    timers.current.push(resolutionTimer);

    const doneTimer = setTimeout(() => {
      setRunning(false);
      setTotalDuration(finishAt);
      setActiveCaseId(caseId);
    }, finishAt + 120);
    timers.current.push(doneTimer);
  };

  const loadScenario = (scenario) => {
    if (running) return;
    setComplaint(scenario.complaint);
    setOrderId(scenario.orderId);
    setScenarioKey(scenario.key);
    setEvents([]);
    setResolution(null);
    setEditingResolution(false);
    setResolutionDraft({ response_en: '', response_bm: '' });
    setTotalDuration(0);
    setErrorMessage('');
  };

  const resolveComplaint = async () => {
    if (running) return;

    setRunning(true);
    setErrorMessage('');
    setEvents([]);
    setResolution(null);
    setTotalDuration(0);

    try {
      const created = await apiFetch('/complaints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          complaint_text: complaint,
          order_id: orderId || null,
        }),
      });

      const apiEvents = await apiFetch(`/complaints/${created.id}/events`);
      const timelineEvents = buildTimelineEvents(apiEvents);
      const nextResolution = buildResolution(created);
      const nextCase = buildCaseFromRecord(created);

      liveCaseId.current = created.id;
      setScenarioKey(orderId ? 'clean' : scenarioKey);
      setCaseRecords((prev) => ({ ...prev, [created.id]: created }));
      setCaseEvents((prev) => ({ ...prev, [created.id]: timelineEvents }));
      setCases((prev) => [nextCase, ...prev.filter((item) => item.id !== created.id)].slice(0, 5));
      setResolutionDraft({
        response_en: nextResolution.response_en,
        response_bm: nextResolution.response_bm,
      });
      setEditingResolution(false);
      scheduleTimeline(timelineEvents, nextResolution, created.id);
    } catch (error) {
      console.error(error);
      setRunning(false);
      setErrorMessage('Could not resolve complaint. Check the backend server and ILMU setup.');
      setEditingResolution(false);
      setEvents([
        { at: 120, agent: 'supervisor', status: 'started', message: 'Pipeline started' },
        { at: 520, agent: 'supervisor', status: 'failed', message: 'Request to backend failed' },
      ]);
    }
  };

  const approve = () => {
    setCases((prev) => prev.map((item) => item.id === liveCaseId.current ? { ...item, status: 'resolved' } : item));
  };

  const startEditingResolution = () => {
    if (!resolution) return;
    setResolutionDraft({
      response_en: resolution.response_en,
      response_bm: resolution.response_bm,
    });
    setEditingResolution(true);
  };

  const cancelEditingResolution = () => {
    setEditingResolution(false);
    setResolutionDraft({
      response_en: resolution?.response_en || '',
      response_bm: resolution?.response_bm || '',
    });
  };

  const saveEditingResolution = () => {
    if (!resolution) return;
    setResolution((prev) => prev ? {
      ...prev,
      response_en: resolutionDraft.response_en,
      response_bm: resolutionDraft.response_bm,
    } : prev);
    if (liveCaseId.current) {
      setCaseRecords((prev) => {
        const current = prev[liveCaseId.current];
        if (!current) return prev;
        return {
          ...prev,
          [liveCaseId.current]: {
            ...current,
            response: {
              ...current.response,
              english: resolutionDraft.response_en,
              bahasa_malaysia: resolutionDraft.response_bm,
            },
          },
        };
      });
    }
    setEditingResolution(false);
  };

  const copyReply = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      console.error(error);
    }
  };

  const openCase = async (caseItem) => {
    setModalCase(caseItem);
    if (caseItem.source !== 'api' || caseEvents[caseItem.complaintId]) return;

    try {
      const apiEvents = await apiFetch(`/complaints/${caseItem.complaintId}/events`);
      setCaseEvents((prev) => ({ ...prev, [caseItem.complaintId]: buildTimelineEvents(apiEvents) }));
    } catch (error) {
      console.error(error);
    }
  };

  let modalResolution = null;
  let modalEvents = [];
  let modalComplaint = null;
  let modalOrderData = null;

  if (modalCase) {
    if (modalCase.source === 'api') {
      const record = caseRecords[modalCase.complaintId];
      modalResolution = record ? buildResolution(record) : null;
      modalEvents = caseEvents[modalCase.complaintId] || [];
      modalComplaint = record?.complaint_text || modalCase.preview;
      modalOrderData = record?.context?.order_data || null;
    } else if (modalCase.id === liveCaseId.current && resolution) {
      modalResolution = resolution;
      modalEvents = events;
      modalComplaint = complaint;
    } else {
      const key = modalCase.resolution === 'REFUND' ? 'manglish' : modalCase.resolution === 'RESHIP' ? 'clean' : 'edge';
      const pipeline = window.PIPELINES[key];
      modalResolution = pipeline.resolution;
      modalEvents = pipeline.events;
      modalComplaint = modalCase.preview;
      modalOrderData = window.MOCK_ORDERS[modalCase.order] || null;
    }
  }

  const approveReplies = resolution ? {
    ...resolution,
    response_en: adjustTone(editingResolution ? resolutionDraft.response_en : resolution.response_en, tone),
    response_bm: adjustTone(editingResolution ? resolutionDraft.response_bm : resolution.response_bm, tone),
  } : null;

  return (
    <div className="app">
      <Topbar
        theme={theme} setTheme={wrap(setTheme, 'theme')}
        density={density} setDensity={wrap(setDensity, 'density')}
        tone={tone} setTone={wrap(setTone, 'tone')}
        traceStyle={traceStyle} setTraceStyle={wrap(setTraceStyle, 'traceStyle')}
        showTweaksUI={false}
      />

      <div className="workspace">
        <ComplaintForm
          complaint={complaint} setComplaint={setComplaint}
          orderId={orderId} setOrderId={setOrderId}
          onResolve={resolveComplaint} running={running}
          scenarios={window.SCENARIOS} onScenario={loadScenario}
        />
        <AgentTracePanel
          events={events} running={running}
          scenario={scenarioKey} traceStyle={traceStyle}
          totalDuration={totalDuration}
        />
        <ResolutionCard
          running={running} resolution={approveReplies}
          onApprove={approve} tone={tone}
          isEditing={editingResolution}
          draft={resolutionDraft}
          onDraftChange={setResolutionDraft}
          onStartEdit={startEditingResolution}
          onCancelEdit={cancelEditingResolution}
          onSaveEdit={saveEditingResolution}
          onCopyReply={copyReply}
          onOpenDetail={() => liveCaseId.current && openCase(cases.find((item) => item.id === liveCaseId.current))}
          scenarioKey={scenarioKey}
        />
      </div>

      {errorMessage && (
        <div className="panel" style={{ marginTop: 14, padding: 16, color: 'var(--warn-fg)', borderColor: 'var(--warn)' }}>
          {errorMessage}
        </div>
      )}

      <CaseLog cases={cases} onOpen={openCase} activeId={activeCaseId} />

      {modalCase && (
        <CaseDetailModal
          caseData={modalCase}
          events={modalEvents}
          resolution={modalResolution}
          scenarioComplaint={modalComplaint}
          orderData={modalOrderData}
          onClose={() => setModalCase(null)}
        />
      )}

      {tweaksHostActive && (
        <TweaksPanel
          open={tweaksUserOpen} setOpen={setTweaksUserOpen}
          theme={theme} setTheme={wrap(setTheme, 'theme')}
          density={density} setDensity={wrap(setDensity, 'density')}
          tone={tone} setTone={wrap(setTone, 'tone')}
          traceStyle={traceStyle} setTraceStyle={wrap(setTraceStyle, 'traceStyle')}
        />
      )}
      {tweaksHostActive && !tweaksUserOpen && (
        <button className="tweaks-fab" onClick={() => setTweaksUserOpen(true)}>
          <span className="tweaks-dot"></span> Tweaks
        </button>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
