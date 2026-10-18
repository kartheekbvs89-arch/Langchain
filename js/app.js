/* ============================================================
   App Shell — Sidebar, Header, Auth Guard, API Client
   Phase 1: standalone mock mode
   Phase 2: connects to Python backend if available
   ============================================================ */

const APP = {
  name: "Enterprise Knowledge Assistant",
  short: "EKA",
  version: "Phase 3 · Cloud + Eval",
};

// ============================================================
// Backend API client — auto-detects if backend is running.
// If backend is unreachable, falls back to mock mode (Phase 1 behaviour).
// ============================================================

const API = (() => {
  // Try multiple possible backend URLs:
  // 1. Explicit override via ?api= query param
  // 2. Same origin (when served by FastAPI at /)
  // 3. Local dev server at http://127.0.0.1:8000
  const override = new URLSearchParams(location.search).get('api');
  const candidates = [
    override,
    '',  // same origin
    'http://127.0.0.1:8000',
    'http://localhost:8000',
  ].filter(Boolean);

  let backendUrl = null;
  let backendChecked = false;

  async function detect() {
    if (backendChecked) return backendUrl;
    backendChecked = true;

    for (const base of candidates) {
      try {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 1500);
        const res = await fetch(`${base}/api/health`, { signal: ctrl.signal });
        clearTimeout(t);
        if (res.ok) {
          const data = await res.json();
          if (data.status === 'ok') {
            backendUrl = base;
            console.info(`[EKA] Backend connected: ${base}`);
            return backendUrl;
          }
        }
      } catch (_) {
        // try next candidate
      }
    }
    console.info('[EKA] Backend not reachable — using Phase 1 mock mode.');
    return null;
  }

  async function request(path, options = {}) {
    const base = await detect();
    if (!base) return null;
    const res = await fetch(`${base}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    });
    if (!res.ok) {
      throw new Error(`API ${res.status}: ${await res.text()}`);
    }
    return res.json();
  }

  return {
    detect,
    isLive: async () => !!(await detect()),
    baseUrl: () => backendUrl,

    health: () => request('/api/health'),
    chat: (question, agent) =>
      request('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ question, agent }),
      }),
    listDocuments: () => request('/api/documents'),
    uploadDocument: (file, agent) => {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('agent', agent);
      return fetch(`${backendUrl}/api/documents/upload`, {
        method: 'POST',
        body: fd,
      }).then(r => r.json());
    },
    deleteDocument: (agent, name) =>
      request(`/api/documents/${agent}/${encodeURIComponent(name)}`, { method: 'DELETE' }),
    analytics: () => request('/api/analytics'),
    seed: () => request('/api/seed', { method: 'POST' }),
    evalSummary: () => request('/api/eval/summary'),
    evalRun: () => request('/api/eval/run', { method: 'POST' }),
    evalLatest: () => request('/api/eval/latest'),
    metrics: () => fetch(`${backendUrl}/api/metrics`).then(r => r.text()),
  };
})();

const AGENTS = [
  {
    id: "hr",
    name: "HR Agent",
    desc: "Leaves, payroll, onboarding, benefits",
    initial: "HR",
    placeholder: "Ask about leaves, payroll, onboarding...",
    suggested: [
      { title: "Leave policy", sub: "How many casual leaves am I entitled to?" },
      { title: "Payroll cycle", sub: "When is the next payroll cut-off?" },
      { title: "Onboarding", sub: "What documents are needed for new hires?" },
      { title: "Benefits", sub: "What is included in the health plan?" },
    ],
    mockReplies: [
      "Based on the HR policy manual (v3.2), employees are entitled to 12 casual leaves, 12 sick leaves, and 15 earned leaves per calendar year. Leaves cannot be carried forward beyond 45 days at year-end. To apply, use the HR Portal under Leaves → Apply, and your manager will be notified for approval. Source: HR_Policy_Manual_2024.pdf, page 14.",
      "The monthly payroll cut-off is the 20th of every month. Any attendance regularization requests must be submitted by the 18th. Salary credits are processed on the last working day. For reimbursement claims, attach bills and submit through the HR Portal before the cut-off to be included in the same cycle. Source: Payroll_Procedure.docx, section 4.2.",
      "Onboarding a new hire requires: (1) signed offer letter, (2) PAN and Aadhaar copies, (3) educational certificates, (4) previous employment relieving letter, (5) bank account details, and (6) two passport-size photographs. The IT and workspace setup happens on Day 1, and HR induction is scheduled on Day 2. Source: Onboarding_Checklist.pdf.",
    ],
  },
  {
    id: "it",
    name: "IT Agent",
    desc: "Access, VPN, hardware, software, tickets",
    initial: "IT",
    placeholder: "Ask about VPN, passwords, hardware, tickets...",
    suggested: [
      { title: "Reset password", sub: "How do I reset my corporate password?" },
      { title: "VPN setup", sub: "How to configure VPN on macOS?" },
      { title: "New laptop", sub: "Request a hardware upgrade" },
      { title: "Software install", sub: "Can I install Python on my machine?" },
    ],
    mockReplies: [
      "To reset your corporate password, go to https://password.company.internal → click 'Forgot Password' → enter your employee ID or email → choose reset via SMS or email OTP → set a new password meeting policy (min 12 chars, 1 uppercase, 1 number, 1 symbol). The new password syncs to Active Directory within 5 minutes. Source: IT_SOP_PasswordReset.pdf.",
      "VPN configuration on macOS: (1) Install Cisco AnyConnect Secure Mobility Client from the IT Self-Service Portal. (2) Open AnyConnect → enter vpn.company.com as the host. (3) Sign in with your corporate credentials + 2FA token from Microsoft Authenticator. (4) Once connected, you'll receive a 10.x.x.x internal IP. If you face MFA issues, contact the IT desk at ext. 4500. Source: IT_Network_Guide_v2.pdf.",
      "Hardware upgrade requests must be raised via the IT Service Portal under 'Request → Hardware → Upgrade'. Approvals follow: Manager → IT Asset Manager → Procurement (if cost > ₹50,000). Standard turnaround is 5 business days. Eligibility: laptop age > 3 years OR performance SLA breach documented by IT. Source: Asset_Policy.docx, clause 7.3.",
    ],
  },
  {
    id: "policy",
    name: "Policy Agent",
    desc: "Code of conduct, compliance, security",
    initial: "PL",
    placeholder: "Ask about company policies and compliance...",
    suggested: [
      { title: "Data classification", sub: "What are the data classification levels?" },
      { title: "Remote work", sub: "Is hybrid work allowed in my role?" },
      { title: "Code of conduct", sub: "What is the gift acceptance policy?" },
      { title: "Information security", sub: "How do I report a phishing email?" },
    ],
    mockReplies: [
      "Company data is classified into four levels: (1) Public — marketing materials, website content; (2) Internal — process docs, org charts; (3) Confidential — employee data, financials, customer PII; (4) Restricted — trade secrets, source code, credentials. Each level has handling, storage, and transmission rules defined in the Information Security Policy v4.0. Source: InfoSec_Policy_v4.pdf, section 2.",
      "Hybrid work eligibility: employees in roles graded L4 and below are eligible for up to 2 days/week remote work, subject to manager approval and team coverage requirements. Roles requiring physical access (lab, data center, facilities) are excluded. Remote work must be from the registered work location; international remote work requires additional Legal and Tax approval. Source: Hybrid_Work_Policy_2024.pdf.",
      "Gift acceptance: employees may accept business gifts up to ₹2,500 in value per occasion. Gifts above this threshold, or any cash/cash-equivalent gifts, must be declined and reported to Compliance within 7 days. Gifts from vendors during active procurement evaluations are strictly prohibited regardless of value. Source: Code_of_Conduct_2024.pdf, section 6.4.",
      "To report a phishing email: (1) Do NOT click any links. (2) Use the 'Report Phishing' button in Outlook (or forward to phishing@company.internal). (3) Delete the email from your inbox. (4) If you already clicked, immediately reset your password and call the IT Security desk at ext. 4700. The SOC team will investigate within 1 business hour. Source: Security_Incident_Response.pdf.",
    ],
  },
];

/* ---------- Auth (mock) ---------- */
function requireAuth() {
  const user = sessionStorage.getItem("eka_user");
  if (!user) {
    window.location.href = "index.html";
    return null;
  }
  return JSON.parse(user);
}

function logout() {
  sessionStorage.removeItem("eka_user");
  window.location.href = "index.html";
}

/* ---------- Sidebar render ---------- */
function renderSidebar(activePage) {
  const user = JSON.parse(sessionStorage.getItem("eka_user") || '{}');
  const navItems = [
    { id: "chat", label: "Chat Assistant", href: "chat.html", icon: chatIcon() },
    { id: "documents", label: "Documents", href: "documents.html", icon: docIcon() },
    { id: "analytics", label: "Analytics", href: "analytics.html", icon: chartIcon() },
  ];

  return `
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-mark">${APP.short.charAt(0)}</div>
        <div>
          <div class="brand-name">${APP.name}</div>
          <div class="brand-sub">${APP.version}</div>
        </div>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-section-title">Workspace</div>
        ${navItems.map(item => `
          <a href="${item.href}" class="nav-item ${item.id === activePage ? 'active' : ''}">
            ${item.icon}
            <span>${item.label}</span>
          </a>
        `).join('')}
        <div class="nav-section-title">Agents</div>
        ${AGENTS.map(a => `
          <a href="chat.html?agent=${a.id}" class="nav-item">
            <span class="agent-icon" style="width:24px;height:24px;font-size:0.625rem;">${a.initial}</span>
            <span>${a.name}</span>
          </a>
        `).join('')}
      </nav>
      <div class="sidebar-footer">
        <div class="user-chip" onclick="logout()" title="Click to logout">
          <div class="user-avatar">${(user.name || 'U').charAt(0)}</div>
          <div class="user-info">
            <div class="user-name">${user.name || 'User'}</div>
            <div class="user-id">${user.email || ''}</div>
          </div>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
        </div>
      </div>
    </aside>
  `;
}

function renderHeader(title, breadcrumb, actions = "") {
  return `
    <header class="header">
      <div class="header-title">
        <div>
          <h2>${title}</h2>
          <div class="header-breadcrumb">${breadcrumb}</div>
        </div>
      </div>
      <div class="header-actions">${actions}</div>
    </header>
  `;
}

/* ---------- Icons ---------- */
function chatIcon() {
  return `<svg class="nav-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>`;
}
function docIcon() {
  return `<svg class="nav-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/>
    <line x1="16" y1="17" x2="8" y2="17"/>
  </svg>`;
}
function chartIcon() {
  return `<svg class="nav-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <line x1="18" y1="20" x2="18" y2="10"/>
    <line x1="12" y1="20" x2="12" y2="4"/>
    <line x1="6" y1="20" x2="6" y2="14"/>
  </svg>`;
}

/* ---------- Mount shell ---------- */
function mountShell(activePage, title, breadcrumb, mainContent, headerActions = "") {
  const user = requireAuth();
  if (!user) return;

  document.body.innerHTML = `
    <div class="app-shell">
      ${renderSidebar(activePage)}
      ${renderHeader(title, breadcrumb, headerActions)}
      <main class="main">
        ${mainContent}
      </main>
    </div>
  `;
}

/* ---------- Backend status pill (shown in header on chat/docs/analytics) ---------- */
async function backendStatusPill() {
  const live = await API.isLive();
  return `<span class="badge"><span class="badge-dot ${live ? 'active' : ''}"></span> ${live ? 'Backend live' : 'Mock mode'}</span>`;
}
