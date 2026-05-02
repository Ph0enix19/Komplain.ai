// Komplain.ai scenarios and simulated agent pipelines.

window.SCENARIOS = [
  {
    key: 'english',
    label: 'English',
    blurb: 'Wrong size',
    complaint: "Hi, I ordered ORD-15 in size M, but the T-shirt I received is size S. The item is not damaged, but it does not match my order. Please arrange the correct size.",
    orderId: 'ORD-15',
  },
  {
    key: 'manglish',
    label: 'Manglish',
    blurb: 'Jaket koyak',
    complaint: "Hi team, saya punya order ORD-26 sampai tapi denim jacket macam koyak dekat sleeve. I already upload gambar, boleh check and help settle?",
    orderId: 'ORD-26',
  },
  {
    key: 'malay',
    label: 'Bahasa',
    blurb: 'But salah',
    complaint: "Saya sudah terima pesanan ORD-37 tetapi but hujan yang diterima ialah warna biru, bukan warna kuning seperti pesanan saya. Saya telah muat naik gambar untuk semakan.",
    orderId: 'ORD-37',
  },
];

window.MOCK_ORDERS = {
  'ORD-15': {
    id: 'ORD-15',
    product_name: 'Classic Cotton T-Shirt - White M',
    order_date: '2026-05-01',
    delivery_status: 'delivered',
    days_since_order: 1,
    seller_policy_refund_days: 7,
    seller_policy_reship_allowed: true,
    courier: 'Ninja Van',
    tracking: 'NV00015MY',
  },
  'ORD-26': {
    id: 'ORD-26',
    product_name: 'Everyday Denim Jacket - Blue L',
    order_date: '2026-04-30',
    delivery_status: 'delivered',
    days_since_order: 3,
    seller_policy_refund_days: 7,
    seller_policy_reship_allowed: true,
    courier: 'J&T Express',
    tracking: 'JT00026MY',
  },
  'ORD-37': {
    id: 'ORD-37',
    product_name: 'Kids Rain Boots - Yellow EU 30',
    order_date: '2026-04-28',
    delivery_status: 'delivered',
    days_since_order: 5,
    seller_policy_refund_days: 7,
    seller_policy_reship_allowed: true,
    courier: 'Pos Laju',
    tracking: 'PL00037MY',
  },
};

window.SEED_CASES = [];

const demoEvents = (languageLabel, orderId) => [
  { at: 120, agent: 'intake', status: 'completed', message: `Intake complete - ${languageLabel}` },
  { at: 280, agent: 'context', status: 'completed', message: `Order found - ${orderId}` },
  { at: 440, agent: 'vision', status: 'completed', message: 'Visual evidence ready' },
  { at: 620, agent: 'reasoning', status: 'completed', message: 'Decision depends on image evidence' },
  { at: 780, agent: 'response', status: 'completed', message: 'Bilingual seller reply ready' },
  { at: 900, agent: 'supervisor', status: 'completed', message: 'Seller review recommended' },
];

window.PIPELINES = {
  english: {
    resolution: {
      type: 'CLARIFY',
      confidence: 0.82,
      reason: 'The customer says ORD-15 arrived in the wrong size. The seller should confirm the size evidence before arranging replacement.',
      policy: 'Wrong item variant review - ORD-15 size mismatch',
      response_en: 'Hi, thanks for letting us know about ORD-15. We are checking the size mismatch before arranging the correct T-shirt size.',
      response_bm: 'Hai, terima kasih kerana memaklumkan kami tentang ORD-15. Kami akan menyemak isu saiz yang tidak sepadan sebelum mengatur saiz baju-T yang betul.',
      amount: '-',
      requires_review: true,
    },
    events: demoEvents('English', 'ORD-15'),
  },
  manglish: {
    resolution: {
      type: 'CLARIFY',
      confidence: 0.82,
      reason: 'Manglish complaint for ORD-26 is understood and awaits the uploaded denim jacket image check.',
      policy: 'Visual evidence required - ORD-26 jacket review',
      response_en: 'Hi, we received your ORD-26 denim jacket complaint and photo. We will check the image evidence before deciding the right resolution.',
      response_bm: 'Hai, kami telah menerima aduan dan gambar jaket denim untuk ORD-26. Kami akan menyemak bukti gambar sebelum menentukan penyelesaian yang sesuai.',
      amount: '-',
      requires_review: true,
    },
    events: demoEvents('Manglish', 'ORD-26'),
  },
  malay: {
    resolution: {
      type: 'CLARIFY',
      confidence: 0.82,
      reason: 'Malay complaint for ORD-37 reports the wrong rain boot color and awaits the uploaded image check.',
      policy: 'Wrong item variant review - ORD-37 color mismatch',
      response_en: 'Hi, we received your ORD-37 rain boot complaint and photo. We will check the visual evidence before confirming a replacement.',
      response_bm: 'Hai, kami telah menerima aduan dan gambar but hujan untuk ORD-37. Kami akan menyemak bukti visual sebelum mengesahkan penggantian.',
      amount: '-',
      requires_review: true,
    },
    events: demoEvents('Malay', 'ORD-37'),
  },
};

window.AGENTS = [
  { key: 'intake', name: 'Intake Agent', role: 'Parses raw complaint - extracts intent, language, urgency' },
  { key: 'context', name: 'Context Agent', role: 'Enriches with order data - policy - delivery status' },
  { key: 'reasoning', name: 'Reasoning Agent', role: '{model} core - applies multi-step policy reasoning' },
  { key: 'response', name: 'Response Agent', role: 'Drafts bilingual EN + BM reply - matches tone' },
  { key: 'supervisor', name: 'Supervisor Agent', role: 'Validates seller-facing outcome - decides review priority' },
];

window.VISION_AGENT = {
  key: 'vision',
  name: 'Visual Evidence',
  role: 'Inspects uploaded image - damage and order match',
};
