OPEN_DATASET_PICKER_JS = """
function openDatasetPicker(inputId) {
  const input = document.getElementById(inputId);
  if (input) {
    input.click();
  }
}
"""

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@400;600;700;800&display=swap');

:root {
  --bg: #0d0f14;
  --surface: #13161e;
  --surface2: #1a1e2a;
  --border: #2a2f3f;
  --accent: #00e5a0;
  --accent2: #ff6b6b;
  --accent3: #7c8cf8;
  --text: #e8eaf2;
  --muted: #6b7280;
  --warn: #f59e0b;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
}

/* ── Header ── */
.app-header {
  background: linear-gradient(135deg, #0d0f14 0%, #13161e 50%, #0d0f14 100%);
  border-bottom: 1px solid var(--border);
  padding: 18px 32px;
  display: flex;
  align-items: center;
  gap: 16px;
  position: sticky;
  top: 0;
  z-index: 100;
}
.app-header h1 {
  font-family: 'Syne', sans-serif;
  font-size: 1.3rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: var(--accent);
}
.header-tag {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 2px 10px;
  color: var(--muted);
  font-size: 11px;
}
.step-badge {
  margin-left: auto;
  display: flex;
  gap: 8px;
}
.step-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--border);
  transition: background 0.3s;
}
.step-dot.active { background: var(--accent); }

/* ── Layout ── */
.main-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  min-height: calc(100vh - 61px);
}

/* ── Sidebar ── */
.sidebar {
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 20px 0;
  overflow-y: auto;
}
.sidebar-section {
  padding: 0 16px 8px;
  margin-bottom: 4px;
}
.sidebar-label {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--muted);
  text-transform: uppercase;
  padding: 12px 16px 6px;
  display: block;
}
.nav-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 16px;
  background: none;
  border: none;
  color: var(--muted);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
  border-left: 2px solid transparent;
  text-align: left;
}
.nav-btn:hover { color: var(--text); background: var(--surface2); }
.nav-btn.active {
  color: var(--accent);
  background: rgba(0,229,160,0.06);
  border-left-color: var(--accent);
}
.nav-icon { font-size: 14px; width: 18px; }

/* ── Content ── */
.content {
  padding: 24px 32px;
  overflow-y: auto;
}
.section-title {
  font-family: 'Syne', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 4px;
}
.section-sub {
  color: var(--muted);
  font-size: 11px;
  margin-bottom: 20px;
}

/* ── Cards ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 18px;
  margin-bottom: 16px;
}
.card-title {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--accent3);
  margin-bottom: 12px;
}

.card > .card-title:not(:first-child) {
  margin-top: 20px;
}

/* ── Stats grid ── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 14px;
  text-align: center;
}
.stat-value {
  font-family: 'Syne', sans-serif;
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--accent);
  display: block;
}
.stat-label {
  font-size: 10px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* ── Table ── */
.df-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 6px;
}
.df-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.df-table thead th {
  background: var(--surface2);
  color: var(--accent3);
  padding: 10px 14px;
  text-align: left;
  font-size: 11px;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  white-space: nowrap;
}
.df-table tbody tr:hover { background: var(--surface2); }
.df-table tbody td {
  padding: 8px 14px;
  border-bottom: 1px solid rgba(42,47,63,0.5);
  color: var(--text);
  white-space: nowrap;
}
.dtype-row-modified { background: rgba(124,140,248,0.08); }
.dtype-cell { min-width: 210px; }
.dtype-cell-head { display: flex; align-items: center; gap: 8px; }
.dtype-cell-modified {
  border-left: 2px solid #5aa7ff;
  background: rgba(90,167,255,0.1);
}
.dtype-picker {
  position: relative;
  min-width: 140px;
}
.dtype-picker > summary {
  list-style: none;
}
.dtype-picker > summary::-webkit-details-marker {
  display: none;
}
.dtype-current {
  display: inline-block;
  background: rgba(124,140,248,0.12);
  border: 1px solid var(--border);
  color: #9cb3ff;
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 11px;
  min-width: 92px;
}
.dtype-picker[open] .dtype-current {
  border-color: #5aa7ff;
  box-shadow: 0 0 0 1px rgba(90,167,255,0.4);
}
.dtype-options {
  position: absolute;
  z-index: 30;
  margin-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 130px;
  background: #0f1320;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.45);
}
.dtype-opt-btn {
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 4px;
  font-size: 11px;
  padding: 5px 8px;
  text-align: left;
  cursor: pointer;
}
.dtype-opt-btn:hover {
  border-color: #5aa7ff;
  color: #b8ceff;
}
.dtype-opt-btn.active {
  background: rgba(90,167,255,0.2);
  border-color: #5aa7ff;
  color: #b8ceff;
}
.dtype-reset-btn {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1px solid rgba(255,107,107,0.4);
  background: rgba(255,107,107,0.14);
  color: #ff9f9f;
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
}
.dtype-reset-btn:hover {
  background: rgba(255,107,107,0.24);
}
.null-cell { color: var(--accent2) !important; font-style: italic; }
.num-cell { color: var(--accent); }

/* ── Form controls ── */
.ctrl-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; margin-bottom: 14px; }
.ctrl-group { display: flex; flex-direction: column; gap: 6px; }
.ctrl-label { font-size: 10px; letter-spacing: 1px; color: var(--muted); text-transform: uppercase; }
select, input[type=text], input[type=number] {
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 7px 12px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  outline: none;
  transition: border-color 0.2s;
}
select.form-select,
select.shiny-input-select,
select.form-select.shiny-bound-input {
  background-color: var(--surface2) !important;
  color: var(--text) !important;
}
select:focus, input:focus { border-color: var(--accent3); }
select option {
  background: var(--surface2);
  color: var(--text);
}

/* ── Buttons ── */
.btn {
  padding: 8px 18px;
  border: none;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
  font-weight: 600;
}
.btn-primary {
  background: var(--accent);
  color: #000;
}
.btn-primary:hover { background: #00c988; transform: translateY(-1px); }
.btn-secondary {
  background: var(--surface2);
  color: var(--text);
  border: 1px solid var(--border);
}
.btn-secondary:hover { border-color: var(--accent3); color: var(--accent3); }
.btn-danger {
  background: rgba(255,107,107,0.15);
  color: var(--accent2);
  border: 1px solid rgba(255,107,107,0.3);
}
.btn-danger:hover { background: rgba(255,107,107,0.25); }

/* ── Progress bar (missing) ── */
.missing-bar-wrap { margin-bottom: 10px; }
.missing-bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.missing-bar-label { width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 11px; color: #ffffff; }
.missing-bar { flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.missing-bar-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg, var(--accent3), var(--accent2)); }
.missing-pct { font-size: 11px; color: var(--muted); width: 40px; text-align: right; }

/* ── Log ── */
.log-box {
  background: #090b10;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 14px;
  font-size: 11px;
  max-height: 200px;
  overflow-y: auto;
  color: var(--accent);
}
.log-line { margin-bottom: 4px; }
.log-line::before { content: '▸ '; color: var(--muted); }

/* ── Pills ── */
.pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 600;
  margin-right: 4px;
}
.pill-num { background: rgba(0,229,160,0.12); color: var(--accent); }
.pill-cat { background: rgba(124,140,248,0.12); color: var(--accent3); }
.pill-miss { background: rgba(255,107,107,0.12); color: var(--accent2); }

/* ── Download area ── */
.download-section {
  border: 1px dashed var(--border);
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  margin-top: 16px;
}
.download-icon { font-size: 2rem; margin-bottom: 10px; display: block; }

/* ── Checkbox list ── */
.check-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 6px; }
.check-item { display: flex; align-items: center; gap: 8px; padding: 6px 10px;
  background: var(--surface2); border: 1px solid var(--border); border-radius: 4px; cursor: pointer; }
.check-item input { accent-color: var(--accent); }
.check-item label { cursor: pointer; font-size: 11px; }

/* ── Diff highlight ── */
.diff-new { color: var(--accent); }
.diff-removed { color: var(--accent2); text-decoration: line-through; }

/* ── Tab strip ── */
.tab-strip { display: flex; gap: 2px; border-bottom: 1px solid var(--border); margin-bottom: 16px; }
.tab-btn {
  padding: 8px 16px; background: none; border: none; border-bottom: 2px solid transparent;
  color: var(--muted); font-family: 'JetBrains Mono', monospace; font-size: 12px;
  cursor: pointer; transition: all 0.15s; margin-bottom: -1px;
}
.tab-btn:hover { color: var(--text); }
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }

/* ── Legend / docs ── */
.legend-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 8px;
    margin-top: 10px;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--surface2);
    font-size: 11px;
}
.legend-swatch { width: 12px; height: 12px; border-radius: 3px; flex: 0 0 12px; }
.doc-panel {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 12px;
}
.doc-panel h3 { color: var(--accent3); font-size: 12px; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }
.doc-panel p, .doc-panel li { color: var(--text); font-size: 12px; }
.plot-card { padding: 12px; }
.info-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: 1px solid var(--border);
    color: var(--accent3);
    text-decoration: none;
    font-size: 11px;
    margin-left: 6px;
}

/* ── Toast notifications ── */
.toast-host {
  position: fixed;
  top: 82px;
  right: 22px;
  z-index: 9999;
  pointer-events: none;
}
.toast-item {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 280px;
  max-width: 420px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #101521;
  color: var(--text);
  padding: 10px 12px;
  box-shadow: 0 12px 34px rgba(0, 0, 0, 0.45);
  animation: toastInOut 3.2s ease forwards;
}
.toast-item i {
  width: 16px;
  text-align: center;
}
.toast-success {
  border-color: rgba(0,229,160,0.45);
  background: rgba(0,229,160,0.13);
}
.toast-success i { color: var(--accent); }
.toast-error {
  border-color: rgba(255,107,107,0.45);
  background: rgba(255,107,107,0.13);
}
.toast-error i { color: var(--accent2); }
.toast-info {
  border-color: rgba(90,167,255,0.45);
  background: rgba(90,167,255,0.13);
}
.toast-info i { color: #8ec5ff; }

@keyframes toastInOut {
  0% {
    opacity: 0;
    transform: translateY(-10px) scale(0.98);
  }
  12% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  86% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateY(-6px) scale(0.98);
  }
}

/* Shiny overrides */
.shiny-input-container { margin-bottom: 0 !important; }
.selectize-control .selectize-input {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 12px !important;
  border-radius: 4px !important;
  box-shadow: none !important;
}
.selectize-control .selectize-input .item {
    color: #ffffff !important;
}
.selectize-dropdown {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
}
.selectize-dropdown .option:hover { background: var(--surface2) !important; }
label { color: var(--muted) !important; font-size: 11px !important; font-family: 'JetBrains Mono', monospace !important; }
.shiny-download-link {
  display: inline-block;
  padding: 10px 24px;
  background: var(--accent);
  color: #000 !important;
  border-radius: 4px;
  text-decoration: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  transition: all 0.15s;
  margin-top: 12px;
}
.shiny-download-link:hover { background: #00c988; transform: translateY(-1px); }
"""
