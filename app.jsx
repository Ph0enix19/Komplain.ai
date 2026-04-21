// Main App — wires everything

const { useState, useEffect, useRef, useCallback } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "light",
  "density": "comfortable",
  "tone": "friendly",
  "traceStyle": "stepper"
}/*EDITMODE-END*/;

function adjustTone(text, tone) {
  if (tone === 'formal') {
    return text.replace(/^Hi there,/, 'Dear Customer,').replace(/^Hi,/, 'Dear Customer,').replace(/— Nadia, Sambal & Silk/, 'Sincerely,\nSambal & Silk Customer Care');
  }
  if (tone === 'technical') {
    return text.replace(/^Hi there,\n\n/, '[AUTO-DRAFT · GLM-4]\n\n').replace(/^Hi,\n\n/, '[AUTO-DRAFT · GLM-4]\n\n');
  }
  return text;
}

function App() {
  // tweak state
  const [theme, setTheme] = useState(TWEAK_DEFAULTS.theme);
  const [density, setDensity] = useState(TWEAK_DEFAULTS.density);
  const [tone, setTone] = useState(TWEAK_DEFAULTS.tone);
  const [traceStyle, setTraceStyle] = useState(TWEAK_DEFAULTS.traceStyle);

  // tweak UI state
  const [tweaksHostActive, setTweaksHostActive] = useState(false);
  const [tweaksUserOpen, setTweaksUserOpen] = useState(false);

  // form state
  const [complaint, setComplaint] = useState(window.SCENARIOS[0].complaint);
  const [orderId, setOrderId] = useState(window.SCENARIOS[0].orderId);
  const [scenarioKey, setScenarioKey] = useState('manglish');

  // pipeline state
  const [events, setEvents] = useState([]);
  const [running, setRunning] = useState(false);
  const [resolution, setResolution] = useState(null);
  const [totalDuration, setTotalDuration] = useState(0);
  const timers = useRef([]);

  // case log + modal
  const [cases, setCases] = useState(window.SEED_CASES);
  const [modalCase, setModalCase] = useState(null);
  const [activeCaseId, setActiveCaseId] = useState(null);
  const liveCaseId = useRef(null);

  // apply theme/density
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-density', density);
  }, [theme, density]);

  // Tweaks protocol
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
  const wrap = (setter, key) => (v) => { setter(v); persist({ [key]: v }); };

  // clean timers
  useEffect(() => () => { timers.current.forEach(clearTimeout); }, []);

  const loadScenario = (s) => {
    if (running) return;
    setComplaint(s.complaint);
    setOrderId(s.orderId);
    setScenarioKey(s.key);
    setEvents([]);
    setResolution(null);
    setTotalDuration(0);
  };

  const resolveComplaint = () => {
    if (running) return;
    // detect scenario from text
    let key = scenarioKey;
    const lower = complaint.toLowerCase();
    if (lower.includes('ord-2041')) key = 'manglish';
    else if (lower.includes('ord-1887')) key = 'clean';
    else if (!orderId && complaint.trim().length < 80) key = 'edge';

    const pipeline = window.PIPELINES[key];
    setScenarioKey(key);
    setEvents([]);
    setResolution(null);
    setRunning(true);

    // create new case row as "live"
    const newId = 'CMP-24A' + (9 + cases.length - window.SEED_CASES.length).toString(16).toUpperCase();
    liveCaseId.current = newId;
    setActiveCaseId(newId);

    timers.current.forEach(clearTimeout);
    timers.current = [];

    pipeline.events.forEach(ev => {
      const t = setTimeout(() => {
        setEvents(prev => [...prev, ev]);
      }, ev.at);
      timers.current.push(t);
    });

    const endAt = pipeline.events[pipeline.events.length - 1].at;
    const resT = setTimeout(() => {
      setResolution(pipeline.resolution);
    }, endAt - 400);
    timers.current.push(resT);

    const doneT = setTimeout(() => {
      setRunning(false);
      setTotalDuration(endAt);
      const r = pipeline.resolution;
      const status = r.type === 'CLARIFY' ? 'pending' : (r.requires_review ? 'review' : 'resolved');
      const now = new Date();
      const ts = `2026-04-21 ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
      const preview = complaint.slice(0, 72) + (complaint.length > 72 ? '…' : '');
      const lang = key === 'manglish' ? 'Manglish' : key === 'edge' ? 'BM' : 'EN';
      const order = orderId || (complaint.match(/ORD-\d+/i)?.[0] || '—');
      setCases(prev => [
        { id: newId, preview, resolution: r.type, confidence: r.confidence, status, timestamp: ts, order, lang },
        ...prev,
      ]);
    }, endAt + 120);
    timers.current.push(doneT);
  };

  const approve = () => {
    setCases(prev => prev.map(c => c.id === liveCaseId.current ? { ...c, status: 'resolved' } : c));
  };

  const openCase = (c) => {
    setModalCase(c);
  };

  // Build resolution for selected case (for modal). If it's the live case, use current resolution + events.
  let modalResolution = null, modalEvents = [], modalComplaint = null;
  if (modalCase) {
    if (modalCase.id === liveCaseId.current && resolution) {
      modalResolution = resolution;
      modalEvents = events;
      modalComplaint = complaint;
    } else {
      // use archived data — map by resolution type to one of the 3 canned pipelines
      const key = modalCase.resolution === 'REFUND' ? 'manglish' : modalCase.resolution === 'RESHIP' ? 'clean' : 'edge';
      const p = window.PIPELINES[key];
      modalResolution = p.resolution;
      modalEvents = p.events;
      modalComplaint = modalCase.preview;
    }
  }

  const approveReplies = resolution ? {
    ...resolution,
    response_en: adjustTone(resolution.response_en, tone),
    response_bm: adjustTone(resolution.response_bm, tone),
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
          onOpenDetail={() => liveCaseId.current && openCase(cases.find(c => c.id === liveCaseId.current))}
          scenarioKey={scenarioKey}
        />
      </div>

      <CaseLog cases={cases} onOpen={openCase} activeId={activeCaseId} />

      {modalCase && (
        <CaseDetailModal
          caseData={modalCase}
          events={modalEvents}
          resolution={modalResolution}
          scenarioComplaint={modalComplaint}
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
