// Main App: wires the static React dashboard to the FastAPI backend.

const { useState, useEffect, useRef } = React;

const HOSTED_API_BASE = 'https://komplaintest.onrender.com/api';
const LOCAL_API_BASE = 'http://127.0.0.1:8000/api';

const API_BASES = (() => {
  if (window.KOMPLAIN_API_BASE) return [window.KOMPLAIN_API_BASE];

  const isLocalFrontend = ['localhost', '127.0.0.1', ''].includes(window.location.hostname);
  if (isLocalFrontend) return [LOCAL_API_BASE, HOSTED_API_BASE];
  return [HOSTED_API_BASE];
})();

let activeApiBase = API_BASES[0];
const DEFAULT_MODEL_LABEL = 'configured model';

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "light",
  "density": "comfortable",
  "tone": "friendly",
  "traceStyle": "stepper"
}/*EDITMODE-END*/;

function modelLabelFromHealth(payload) {
  return payload?.llm_model || window.KOMPLAIN_MODEL_LABEL || DEFAULT_MODEL_LABEL;
}

function replaceModelToken(text, modelLabel) {
  return String(text || '')
    .replace(/\{model\}/g, modelLabel)
    .replace(/\bGLM-5\.1\b/g, modelLabel);
}

function getDisplayAgents(modelLabel) {
  return window.AGENTS.map((agent) => ({
    ...agent,
    role: replaceModelToken(agent.role, modelLabel),
  }));
}

function materializeDemoPipeline(pipeline, modelLabel) {
  if (!pipeline) return pipeline;
  return {
    ...pipeline,
    events: pipeline.events.map((event) => ({
      ...event,
      message: replaceModelToken(event.message, modelLabel),
    })),
  };
}

function shouldWarnForConfidence(value) {
  return Number(value || 0) < 0.8;
}

function adjustTone(text, tone, modelLabel = DEFAULT_MODEL_LABEL) {
  if (tone === 'formal') {
    return text
      .replace(/^Hi there,/, 'Dear Customer,')
      .replace(/^Hi,/, 'Dear Customer,')
      .replace(/(?:--|\u2014) Komplain.ai Support/g, 'Sincerely,\nCustomer Support');
  }
  if (tone === 'technical') {
    return text
      .replace(/^Hi there,\n\n/, `[AUTO-DRAFT - ${modelLabel}]\n\n`)
      .replace(/^Hi,\n\n/, `[AUTO-DRAFT - ${modelLabel}]\n\n`);
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

function formatDurationMs(value) {
  return `${(Number(value || 0) / 1000).toFixed(2)}s`;
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
  return record.reasoning.requires_human_review && shouldWarnForConfidence(record.reasoning.confidence) ? 'review' : 'resolved';
}

function buildAmount(record) {
  const decision = record.reasoning.decision;
  const order = record.context.order_data;
  if (decision === 'REFUND' && order?.total && order?.currency) {
    return `${order.currency} ${Number(order.total).toFixed(2)}`;
  }
  if (decision === 'RESHIP') return '1 x replacement';
  return '-';
}

function buildPolicy(record) {
  if (!record.context.order_found && !record.intake.order_id) return 'Supervisor review - missing order ID';
  if (!record.context.order_found) return 'Supervisor review - order lookup failed';
  if (record.reasoning.decision === 'REFUND') return 'Order policy - refund path selected';
  if (record.reasoning.decision === 'RESHIP') return 'Order policy - replacement path selected';
  return 'Supervisor logic - manual review';
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
    review_warning: record.reasoning.requires_human_review && shouldWarnForConfidence(record.reasoning.confidence),
    total_latency: record.total_latency || 0,
    total_tokens: record.total_tokens || 0,
    estimated_cost_rm: record.estimated_cost_rm || 0,
  };
}

function buildCaseFromRecord(record) {
  const resolution = buildResolution(record);
  return {
    id: record.id,
    displayId: buildDisplayCaseId(record.id),
    preview: record.complaint_text.slice(0, 72) + (record.complaint_text.length > 72 ? '...' : ''),
    resolution: resolution.type,
    confidence: record.reasoning.confidence,
    status: buildCaseStatus(record),
    timestamp: formatTimestamp(record.created_at),
    order: record.intake.order_id || '-',
    lang: record.intake.language || inferLanguage(record.complaint_text),
    complaintId: record.id,
    source: 'api',
    totalLatency: record.total_latency || 0,
    totalTokens: record.total_tokens || 0,
    estimatedCostRm: record.estimated_cost_rm || 0,
  };
}

function buildTimelineEvents(apiEvents, modelLabel = DEFAULT_MODEL_LABEL) {
  const events = [];
  let cursor = 0;

  apiEvents.forEach((event) => {
    const isContextFailure = event.step === 'context' && event.payload?.order_found === false;
    const duration = Number(event.duration ?? event.payload?.duration ?? 0);
    const durationMs = Math.max(0, Math.round(duration * 1000));
    const startedAt = cursor;
    const finishedAt = cursor + durationMs;
    const telemetry = {
      duration,
      input_tokens: event.input_tokens ?? event.payload?.input_tokens ?? 0,
      output_tokens: event.output_tokens ?? event.payload?.output_tokens ?? 0,
      execution_mode: event.execution_mode ?? event.payload?.execution_mode ?? 'unknown',
      provider_used: event.provider_used ?? event.payload?.provider_used,
      fallback_used: Boolean(event.fallback_used ?? event.payload?.fallback_used),
      fallback_reason: event.fallback_reason ?? event.payload?.fallback_reason,
    };

    events.push({
      at: finishedAt,
      startAt: startedAt,
      endAt: finishedAt,
      agent: event.step,
      status: isContextFailure ? 'failed' : 'completed',
      message: replaceModelToken(event.message, modelLabel),
      output: event.payload,
      ...telemetry,
    });
    cursor = finishedAt;
  });

  return events;
}

async function apiFetch(path, options) {
  const candidates = [activeApiBase, ...API_BASES.filter((base) => base !== activeApiBase)];
  let lastError = null;

  for (const base of candidates) {
    try {
      const response = await fetch(`${base}${path}`, options);
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Request failed with ${response.status}`);
      }
      activeApiBase = base;
      return response.json();
    } catch (error) {
      lastError = error;
      const canTryNextApi = error instanceof TypeError && candidates.indexOf(base) < candidates.length - 1;
      if (!canTryNextApi) throw error;
      console.warn(`API at ${base} is unavailable, trying fallback.`, error);
    }
  }

  throw lastError || new Error('API request failed.');
}

async function pollForCompletion(complaintId, onEvents, modelLabel = DEFAULT_MODEL_LABEL) {
  const pollIntervalMs = 1500;
  const maxWaitMs = 8 * 60 * 1000;
  const startedAt = Date.now();
  let record = { id: complaintId, status: 'PROCESSING' };

  while (record.status === 'PROCESSING') {
    if (Date.now() - startedAt > maxWaitMs) {
      throw new Error('Timed out waiting for pipeline to complete.');
    }
    await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
    try {
      const [next, apiEvents] = await Promise.all([
        apiFetch(`/complaints/${complaintId}`),
        apiFetch(`/complaints/${complaintId}/events`),
      ]);
      record = next;
      if (typeof onEvents === 'function') {
        onEvents(buildTimelineEvents(apiEvents, modelLabel));
      }
    } catch (error) {
      console.warn('Polling tick failed, retrying', error);
    }
  }

  return record;
}

function App() {
  const [theme, setTheme] = useState(TWEAK_DEFAULTS.theme);
  const [density, setDensity] = useState(TWEAK_DEFAULTS.density);
  const [tone, setTone] = useState(TWEAK_DEFAULTS.tone);
  const [traceStyle, setTraceStyle] = useState(TWEAK_DEFAULTS.traceStyle);
  const [modelLabel, setModelLabel] = useState(window.KOMPLAIN_MODEL_LABEL || DEFAULT_MODEL_LABEL);
  const agents = React.useMemo(() => getDisplayAgents(modelLabel), [modelLabel]);

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

  const [cases, setCases] = useState(window.SEED_CASES || []);
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
    const onMsg = (event) => {
      if (!event.data || typeof event.data !== 'object') return;
      if (event.data.type === '__activate_edit_mode') {
        setTweaksHostActive(true);
        setTweaksUserOpen(true);
      }
      if (event.data.type === '__deactivate_edit_mode') {
        setTweaksHostActive(false);
        setTweaksUserOpen(false);
      }
    };
    window.addEventListener('message', onMsg);
    window.parent.postMessage({ type: '__edit_mode_available' }, '*');
    return () => window.removeEventListener('message', onMsg);
  }, []);

  const persist = (edits) => window.parent.postMessage({ type: '__edit_mode_set_keys', edits }, '*');
  const wrap = (setter, key) => (value) => {
    setter(value);
    persist({ [key]: value });
  };

  useEffect(() => {
    let cancelled = false;

    async function loadComplaints() {
      try {
        try {
          const health = await apiFetch('/health');
          if (!cancelled) setModelLabel(modelLabelFromHealth(health));
        } catch (error) {
          console.warn('Could not load model metadata', error);
        }
        const records = await apiFetch('/complaints');
        if (cancelled) return;
        const completed = records.filter((record) => record && record.intake && record.context && record.reasoning && record.response);
        const mapped = [...completed]
          .sort((a, b) => parseTimestamp(b.created_at) - parseTimestamp(a.created_at))
          .map(buildCaseFromRecord);
        const recordMap = completed.reduce((acc, record) => {
          acc[record.id] = record;
          return acc;
        }, {});
        setCaseRecords(recordMap);
        setCases(mapped.length ? mapped.slice(0, 5) : (window.SEED_CASES || []));
      } catch (error) {
        console.error(error);
        if (!cancelled) {
          setErrorMessage('Local backend is offline, so the dashboard is showing sample cases. Start the backend on port 8000 or use the hosted API fallback when running a complaint.');
          setCases(window.SEED_CASES || []);
        }
      }
    }

    loadComplaints();
    return () => { cancelled = true; };
  }, []);

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

  const resetWorkspace = () => {
    // Clear the live workspace after the final approval so the next case starts fresh.
    setComplaint('');
    setOrderId('');
    setScenarioKey('');
    setEvents([]);
    setResolution(null);
    setEditingResolution(false);
    setResolutionDraft({ response_en: '', response_bm: '' });
    setTotalDuration(0);
    setRunning(false);
    setErrorMessage('');
    setActiveCaseId(null);
    setModalCase(null);
    liveCaseId.current = null;
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

      liveCaseId.current = created.id;
      const final = await pollForCompletion(created.id, (liveEvents) => {
        setEvents(liveEvents);
        setCaseEvents((prev) => ({ ...prev, [created.id]: liveEvents }));
      }, modelLabel);

      if (final.status === 'FAILED') {
        throw new Error(final.error || 'Pipeline failed');
      }

      const apiEvents = await apiFetch(`/complaints/${final.id}/events`);
      const timelineEvents = buildTimelineEvents(apiEvents, modelLabel);
      const nextResolution = buildResolution(final);
      const nextCase = buildCaseFromRecord(final);
      const lastTimelineEvent = timelineEvents[timelineEvents.length - 1];
      const finishAt = final.total_latency ? Math.round(final.total_latency * 1000) : (lastTimelineEvent?.at || 0);

      setCaseRecords((prev) => ({ ...prev, [final.id]: final }));
      setCaseEvents((prev) => ({ ...prev, [final.id]: timelineEvents }));
      setCases((prev) => [nextCase, ...prev.filter((item) => item.id !== final.id)].slice(0, 5));
      setResolutionDraft({
        response_en: nextResolution.response_en,
        response_bm: nextResolution.response_bm,
      });
      setEditingResolution(false);
      setEvents(timelineEvents);
      setResolution(nextResolution);
      setTotalDuration(finishAt);
      setActiveCaseId(final.id);
      setRunning(false);
    } catch (error) {
      console.error(error);
      setRunning(false);
      setErrorMessage('Could not resolve complaint. Start the local backend with a valid LLM setup, or confirm the hosted API is reachable.');
      setEditingResolution(false);
      setEvents([{ at: 0, agent: 'supervisor', status: 'failed', message: 'Request to backend failed' }]);
    }
  };

  const approve = () => {
    const approvedId = liveCaseId.current;
    if (approvedId) {
      setCases((prev) => prev.map((item) => item.id === approvedId ? { ...item, status: 'resolved' } : item));
    }
    resetWorkspace();
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
    return navigator.clipboard.writeText(text);
  };

  const openCase = async (caseItem) => {
    if (!caseItem) return;
    setModalCase(caseItem);
    if (caseItem.source !== 'api' || caseEvents[caseItem.complaintId]) return;

    try {
      const apiEvents = await apiFetch(`/complaints/${caseItem.complaintId}/events`);
      setCaseEvents((prev) => ({ ...prev, [caseItem.complaintId]: buildTimelineEvents(apiEvents, modelLabel) }));
    } catch (error) {
      console.error(error);
    }
  };

  const openLiveCaseDetail = () => {
    if (!liveCaseId.current) return;
    const activeCase = cases.find((item) => item.id === liveCaseId.current);
    if (activeCase) openCase(activeCase);
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
      const key = modalCase.resolution === 'REFUND' ? 'manglish' : modalCase.resolution === 'RESHIP' ? 'wrong' : 'edge';
      const pipeline = materializeDemoPipeline(window.PIPELINES[key], modelLabel);
      modalResolution = pipeline.resolution;
      modalEvents = pipeline.events;
      modalComplaint = modalCase.preview;
      modalOrderData = window.MOCK_ORDERS[modalCase.order] || null;
    }
  }

  const approveReplies = resolution ? {
    ...resolution,
    response_en: adjustTone(editingResolution ? resolutionDraft.response_en : resolution.response_en, tone, modelLabel),
    response_bm: adjustTone(editingResolution ? resolutionDraft.response_bm : resolution.response_bm, tone, modelLabel),
  } : null;

  return (
    <div className="app">
      <Topbar
        theme={theme}
        setTheme={wrap(setTheme, 'theme')}
        density={density}
        setDensity={wrap(setDensity, 'density')}
        modelLabel={modelLabel}
      />

      <CommandCenter
        cases={cases}
        running={running}
        resolution={approveReplies}
        events={events}
        totalDuration={totalDuration}
        tone={tone}
        setTone={wrap(setTone, 'tone')}
        traceStyle={traceStyle}
        setTraceStyle={wrap(setTraceStyle, 'traceStyle')}
        onResolve={resolveComplaint}
        canResolve={Boolean(complaint.trim())}
        agents={agents}
      />

      <div className="workspace">
        <ComplaintForm
          complaint={complaint}
          setComplaint={setComplaint}
          orderId={orderId}
          setOrderId={setOrderId}
          onResolve={resolveComplaint}
          running={running}
          scenarios={window.SCENARIOS}
          onScenario={loadScenario}
          activeScenario={scenarioKey}
          modelLabel={modelLabel}
          agents={agents}
        />
        <AgentTracePanel
          events={events}
          running={running}
          scenario={scenarioKey}
          traceStyle={traceStyle}
          totalDuration={totalDuration}
          agents={agents}
        />
        <ResolutionCard
          running={running}
          resolution={approveReplies}
          onApprove={approve}
          tone={tone}
          isEditing={editingResolution}
          draft={resolutionDraft}
          onDraftChange={setResolutionDraft}
          onStartEdit={startEditingResolution}
          onCancelEdit={cancelEditingResolution}
          onSaveEdit={saveEditingResolution}
          onCopyReply={copyReply}
          onOpenDetail={openLiveCaseDetail}
        />
      </div>

      {errorMessage && (
        <div className="case-log alert alert-warning" role="alert">
          <span className="badge badge-warn">Notice</span>
          <span>{errorMessage}</span>
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
          agents={agents}
          onClose={() => setModalCase(null)}
        />
      )}

      {tweaksHostActive && (
        <TweaksPanel
          open={tweaksUserOpen}
          setOpen={setTweaksUserOpen}
          theme={theme}
          setTheme={wrap(setTheme, 'theme')}
          density={density}
          setDensity={wrap(setDensity, 'density')}
          tone={tone}
          setTone={wrap(setTone, 'tone')}
          traceStyle={traceStyle}
          setTraceStyle={wrap(setTraceStyle, 'traceStyle')}
        />
      )}
      {tweaksHostActive && !tweaksUserOpen && (
        <button className="tweaks-fab" type="button" onClick={() => setTweaksUserOpen(true)}>
          <span className="tweaks-dot" aria-hidden="true"></span> Tweaks
        </button>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
