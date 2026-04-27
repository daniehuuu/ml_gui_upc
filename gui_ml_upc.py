from pathlib import Path

from shiny import App, ui, render, reactive
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64
import json
import warnings
warnings.filterwarnings("ignore")

# ─── CSS ────────────────────────────────────────────────────────────────────
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
select:focus, input:focus { border-color: var(--accent3); }
select option { background: var(--surface2); }

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

# ─── UI ────────────────────────────────────────────────────────────────────
app_ui = ui.page_fluid(
    ui.tags.style(CUSTOM_CSS),
    ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),

    # ── Header
    ui.div(
        ui.div(
            ui.tags.h1("DataPrep Studio"),
            ui.span("v1.0", class_="header-tag"),
            ui.span("// Shiny for Python", class_="header-tag"),
            class_="app-header"
        ),
    ),

    # ── Main layout
    ui.div(
        # ── Sidebar
        ui.div(
            ui.tags.span("PIPELINE", class_="sidebar-label"),
            ui.output_ui("sidebar_nav"),

            ui.tags.span("ESTADO", class_="sidebar-label"),
            ui.div(ui.output_ui("sidebar_status"), style="padding: 0 16px;"),

                        ui.tags.script("""
                            function openDatasetPicker(inputId) {
                                const input = document.getElementById(inputId);
                                if (input) {
                                    input.click();
                                }
                            }
                        """),

            class_="sidebar"
        ),

        # ── Content
        ui.div(
            ui.output_ui("main_content"),
            class_="content"
        ),

        class_="main-layout"
    ),

    # Hidden: upload
    ui.div(
        ui.input_file("upload_csv", "", accept=[".csv"]),
        style="display:none"
    )
)

# ─── Server ────────────────────────────────────────────────────────────────
def server(input, output, session):

    # ── State
    current_page = reactive.Value("overview")
    df_original = reactive.Value(None)
    df_current  = reactive.Value(None)
    ops_log     = reactive.Value([])
    load_config = reactive.Value({"separator": ";", "custom_separator": "|", "header": "infer", "encoding": "utf-8"})

    separator_options = {
        ",": "Coma ( , )",
        ";": "Punto y coma ( ; )",
        "\t": "Tab",
        "custom": "Personalizado",
    }

    missing_categories = [
        (0, 0.01, "Trivial", "var(--accent)", "< 1%"),
        (0.01, 0.05, "Manejable", "#7c8cf8", "[1%, 5%)"),
        (0.05, 0.15, "Sofisticado", "#f59e0b", "[5%, 15%)"),
        (0.15, 1.0, "Perjudicial", "var(--accent2)", "> 15%"),
    ]

    def resolve_separator():
        choice = input.load_sep() if hasattr(input, "load_sep") else ";"
        if choice == "custom":
            custom_value = (input.load_custom_sep() if hasattr(input, "load_custom_sep") else "") or "|"
            return custom_value
        return choice or ";"

    def resolve_header():
        header_choice = input.load_header() if hasattr(input, "load_header") else "infer"
        return None if header_choice == "none" else 0

    def resolve_encoding():
        encoding_value = input.load_encoding() if hasattr(input, "load_encoding") else "utf-8"
        return encoding_value or "utf-8"

    def load_csv_file(file_path, file_name=None):
        separator = resolve_separator()
        header = resolve_header()
        encoding = resolve_encoding()
        last_error = None

        for trial_encoding in [encoding, "utf-8", "latin1"]:
            try:
                df = pd.read_csv(
                    file_path,
                    sep=separator,
                    header=header,
                    encoding=trial_encoding,
                    engine="python",
                )
                load_config.set({
                    "separator": separator,
                    "custom_separator": input.load_custom_sep() if hasattr(input, "load_custom_sep") else "",
                    "header": "infer" if header == 0 else "none",
                    "encoding": trial_encoding,
                })
                df_original.set(df.copy())
                df_current.set(df.copy())
                ops_log.set([
                    f"Dataset cargado: {file_name or Path(file_path).name} ({df.shape[0]} filas × {df.shape[1]} cols)",
                    f"Separador: {separator!r} | cabecera: {'inferida' if header == 0 else 'sin cabecera'} | encoding: {trial_encoding}",
                ])
                return df, None
            except Exception as exc:
                last_error = exc

        return None, f"No fue posible leer el archivo con separador {separator!r}. Error: {last_error}"

    def html_figure(fig, height=420):
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=24, r=24, t=40, b=24),
            height=height,
            font=dict(family="JetBrains Mono, monospace", color="#e8eaf2"),
        )
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"displayModeBar": False}))

    def missing_category_for_pct(pct):
        for low, high, label, color, _ in missing_categories:
            if low <= pct < high:
                return label, color
        return "Perjudicial", "var(--accent2)"

    def outlier_category_for_pct(pct):
        if pct == 0:
            return "Sin outliers", "var(--accent)"
        if pct < 1:
            return "Leve", "var(--accent)"
        if pct < 5:
            return "Moderado", "#7c8cf8"
        if pct < 15:
            return "Alto", "#f59e0b"
        return "Crítico", "var(--accent2)"

    # ── Load default CSV on startup
    @reactive.Effect
    def _load_default():
        try:
            default_path = Path(__file__).resolve().with_name("bupa.csv")
            if not default_path.exists():
                default_path = Path(__file__).resolve().parent / "bupa.csv"
            df, error_message = load_csv_file(str(default_path), default_path.name)
            if error_message:
                ops_log.set([error_message])
        except Exception as e:
            ops_log.set([f"Error al cargar dataset: {e}"])

    # ── Navigation
    @reactive.Effect
    @reactive.event(input.nav_overview)
    def _(): current_page.set("overview")

    @reactive.Effect
    @reactive.event(input.nav_eda)
    def _(): current_page.set("eda")

    @reactive.Effect
    @reactive.event(input.nav_missing)
    def _(): current_page.set("missing")

    @reactive.Effect
    @reactive.event(input.nav_encode)
    def _(): current_page.set("encode")

    @reactive.Effect
    @reactive.event(input.nav_scale)
    def _(): current_page.set("scale")

    @reactive.Effect
    @reactive.event(input.nav_outlier)
    def _(): current_page.set("outlier")

    @reactive.Effect
    @reactive.event(input.nav_drop)
    def _(): current_page.set("drop")

    @reactive.Effect
    @reactive.event(input.nav_export)
    def _(): current_page.set("export")

    @reactive.Effect
    @reactive.event(input.nav_docs)
    def _(): current_page.set("docs")

    # ── Upload new CSV
    @reactive.Effect
    @reactive.event(input.upload_csv)
    def _handle_upload():
        f = input.upload_csv()
        if f:
            load_csv_file(f[0]["datapath"], f[0]["name"])

    # ── Helpers
    def get_num_cols(df):
        return df.select_dtypes(include=np.number).columns.tolist()

    def get_cat_cols(df):
        return df.select_dtypes(include="object").columns.tolist()

    def add_log(msg):
        ops_log.set(ops_log() + [msg])

    def df_preview_html(df, max_rows=8):
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        rows = ""
        for _, row in df.head(max_rows).iterrows():
            cells = ""
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    cells += f'<td class="null-cell">NaN</td>'
                elif col in num_cols:
                    cells += f'<td class="num-cell">{val}</td>'
                else:
                    cells += f'<td>{val}</td>'
            rows += f"<tr>{cells}</tr>"
        headers = "".join(f"<th>{c}</th>" for c in df.columns)
        return f"""
        <div class="df-table-wrap">
          <table class="df-table">
            <thead><tr>{headers}</tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        <div style="color:var(--muted);font-size:11px;margin-top:6px;">
          Mostrando {min(max_rows, len(df))} de {len(df)} filas · {df.shape[1]} columnas
        </div>
        """

    def missing_report_html(df):
        rows = []
        for col in df.columns:
            missing_count = int(df[col].isna().sum())
            missing_pct = round(100 * missing_count / len(df), 2) if len(df) else 0
            category, color = missing_category_for_pct(missing_pct / 100 if missing_pct else 0)
            rows.append(
                f"<tr><td>{col}</td><td>{missing_count}</td><td>{missing_pct}%</td><td><span class='pill' style='background:{color};color:#fff'>{category}</span></td></tr>"
            )
        legend = "".join(
            f"<div class='legend-item'><span class='legend-swatch' style='background:{color}'></span><div><strong>{label}</strong><div style='color:var(--muted)'>{range_text}</div></div></div>"
            for _, _, label, color, range_text in missing_categories
        )
        return f"""
        <div class="df-table-wrap">
          <table class="df-table">
            <thead><tr><th>Columna</th><th>Nulos</th><th>%</th><th>Categoría</th></tr></thead>
            <tbody>{''.join(rows)}</tbody>
          </table>
        </div>
        <div class="legend-grid">{legend}</div>
        """

    def outlier_report_html(df, method="iqr", z_threshold=3.0):
        num_cols = get_num_cols(df)
        rows = []
        for col in num_cols:
            series = df[col].dropna()
            if series.empty:
                continue
            if method == "zscore":
                mean = series.mean()
                std = series.std(ddof=0) or 1
                outliers = ((series - mean).abs() > z_threshold * std).sum()
                method_label = f"Z-score ±{z_threshold}σ"
            else:
                q1, q3 = series.quantile(0.25), series.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = ((series < lower) | (series > upper)).sum()
                method_label = "IQR"
            pct = round(100 * outliers / len(series), 2)
            category, color = outlier_category_for_pct(pct)
            rows.append(
                f"<tr><td>{col}</td><td>{outliers}</td><td>{pct}%</td><td><span class='pill' style='background:{color};color:#fff'>{category}</span></td><td>{method_label}</td></tr>"
            )
        legend = """
        <div class="legend-grid">
          <div class="legend-item"><span class="legend-swatch" style="background:var(--accent)"></span><div><strong>Leve</strong><div style="color:var(--muted)">&lt; 1%</div></div></div>
          <div class="legend-item"><span class="legend-swatch" style="background:#7c8cf8"></span><div><strong>Moderado</strong><div style="color:var(--muted)">[1%, 5%)</div></div></div>
          <div class="legend-item"><span class="legend-swatch" style="background:#f59e0b"></span><div><strong>Alto</strong><div style="color:var(--muted)">[5%, 15%)</div></div></div>
          <div class="legend-item"><span class="legend-swatch" style="background:var(--accent2)"></span><div><strong>Crítico</strong><div style="color:var(--muted)">&gt;= 15%</div></div></div>
        </div>
        """
        return f"""
        <div class="df-table-wrap">
          <table class="df-table">
            <thead><tr><th>Columna</th><th>Outliers</th><th>%</th><th>Categoría</th><th>Método</th></tr></thead>
            <tbody>{''.join(rows) if rows else '<tr><td colspan="5">Sin columnas numéricas</td></tr>'}</tbody>
          </table>
        </div>
        {legend}
        """

    def make_corr_heatmap(df, columns, method):
        corr = df[columns].corr(method=method)
        fig = px.imshow(
            corr,
            text_auto=True,
            color_continuous_scale=[[0, "#0d0f14"], [0.5, "#7c8cf8"], [1, "#00e5a0"]],
            zmin=-1,
            zmax=1,
            aspect="auto",
        )
        fig.update_layout(title=f"Matriz de correlación ({method.title()})")
        return fig

    def make_distribution_figure(df, column, plot_kind):
        series = df[column].dropna()
        fig = go.Figure()
        if plot_kind in {"hist", "hist_density"}:
            fig.add_trace(go.Histogram(x=series, nbinsx=min(30, max(10, int(np.sqrt(len(series))))), name="Histograma", marker_color="#00e5a0", opacity=0.8))
            if plot_kind == "hist_density":
                fig.add_trace(go.Histogram(x=series, histnorm="probability density", nbinsx=min(30, max(10, int(np.sqrt(len(series))))), name="Densidad", marker_color="#7c8cf8", opacity=0.45))
        elif plot_kind == "box":
            fig.add_trace(go.Box(y=series, name=column, marker_color="#ff6b6b", boxmean=True))
        fig.update_layout(title=f"{column} - {plot_kind.replace('_', ' ').title()}")
        return fig

    # ─────────────────────────────────────────────────────────────
    # OVERVIEW PAGE
    # ─────────────────────────────────────────────────────────────
    def render_overview(df):
        if df is None:
            return ui.div(
                ui.div(ui.tags.h2("Dataset Overview", class_="section-title"),
                       ui.p("Carga un dataset para empezar a trabajar", class_="section-sub")),
                ui.div(
                    ui.tags.label("Carga configurable:", style="color:var(--muted);font-size:11px;display:block;margin-bottom:6px;"),
                    ui.tags.button("Cargar archivo", type="button", onclick="openDatasetPicker('upload_csv2')", class_="btn btn-primary"),
                    ui.div(
                        ui.div(ui.input_file("upload_csv2", "", accept=[".csv", ".tsv", ".txt"]), style="display:none"),
                        ui.div(ui.input_select("load_sep", "Separador", separator_options, selected=load_config()["separator"]), class_="ctrl-group"),
                        ui.div(ui.input_text("load_custom_sep", "Separador personalizado", value=load_config()["custom_separator"]), class_="ctrl-group"),
                        ui.div(ui.input_select("load_header", "Cabecera", {"infer": "Con cabecera", "none": "Sin cabecera"}, selected=load_config()["header"]), class_="ctrl-group"),
                        ui.div(ui.input_text("load_encoding", "Encoding", value=load_config()["encoding"]), class_="ctrl-group"),
                        class_="ctrl-row"
                    ),
                    ui.div(ui.tags.small("El botón de archivo abre el selector del sistema. La configuración se conserva durante la sesión."), style="color:var(--muted);"),
                    class_="card"
                ),
                ui.div(
                    ui.div("ESTADO", class_="card-title"),
                    ui.div("No hay dataset cargado todavía. Usa el botón anterior para seleccionar un archivo.", style="color:var(--muted);"),
                    class_="card"
                )
            )

        n_rows, n_cols = df.shape
        num_cols = get_num_cols(df)
        cat_cols = get_cat_cols(df)
        total_missing = df.isnull().sum().sum()
        miss_pct = round(100 * total_missing / (n_rows * n_cols), 1)

        # Missing bars
        missing_per_col = df.isnull().sum()
        missing_per_col = missing_per_col[missing_per_col > 0].sort_values(ascending=False)
        miss_bars = ""
        for col, cnt in missing_per_col.items():
            pct = round(100 * cnt / n_rows, 1)
            miss_bars += f"""
            <div class="missing-bar-row">
              <span class="missing-bar-label">{col}</span>
              <div class="missing-bar"><div class="missing-bar-fill" style="width:{pct}%"></div></div>
              <span class="missing-pct">{pct}%</span>
            </div>
            """
        if not miss_bars:
            miss_bars = '<span style="color:var(--accent)">✓ Sin valores faltantes</span>'

        # Dtype table
        dtype_rows = ""
        for col in df.columns:
            dtype = str(df[col].dtype)
            n_unique = df[col].nunique()
            n_null = df[col].isnull().sum()
            kind = "pill-num" if col in num_cols else "pill-cat"
            kind_label = "num" if col in num_cols else "cat"
            dtype_rows += f"""
            <tr>
              <td>{col}</td>
              <td><span class="pill {kind}">{kind_label}</span></td>
              <td>{dtype}</td>
              <td>{n_unique}</td>
              <td>{'<span style="color:var(--accent2)">' + str(n_null) + '</span>' if n_null > 0 else n_null}</td>
            </tr>
            """

        return ui.div(
            ui.div(ui.tags.h2("Dataset Overview", class_="section-title"),
                   ui.p("Resumen general del dataset cargado", class_="section-sub")),

            # Upload button
            ui.div(
                ui.tags.label("Carga configurable:", style="color:var(--muted);font-size:11px;display:block;margin-bottom:6px;"),
                ui.tags.button("Cargar archivo", type="button", onclick="openDatasetPicker('upload_csv2')", class_="btn btn-primary"),
                ui.div(
                    ui.div(ui.input_file("upload_csv2", "", accept=[".csv", ".tsv", ".txt"]), style="display:none"),
                    ui.div(ui.input_select("load_sep", "Separador", separator_options, selected=load_config()["separator"]), class_="ctrl-group"),
                    ui.div(ui.input_text("load_custom_sep", "Separador personalizado", value=load_config()["custom_separator"]), class_="ctrl-group"),
                    ui.div(ui.input_select("load_header", "Cabecera", {"infer": "Con cabecera", "none": "Sin cabecera"}, selected=load_config()["header"]), class_="ctrl-group"),
                    ui.div(ui.input_text("load_encoding", "Encoding", value=load_config()["encoding"]), class_="ctrl-group"),
                    class_="ctrl-row"
                ),
                ui.div(ui.tags.small("La configuración se aplica al momento de cargar el archivo y se conserva durante la sesión."), style="color:var(--muted);"),
                class_="card", style="margin-bottom:16px;"
            ),

            # Stats
            ui.div(
                ui.div(ui.tags.span(str(n_rows), class_="stat-value"), ui.tags.span("FILAS", class_="stat-label"), class_="stat-card"),
                ui.div(ui.tags.span(str(n_cols), class_="stat-value"), ui.tags.span("COLUMNAS", class_="stat-label"), class_="stat-card"),
                ui.div(ui.tags.span(str(len(num_cols)), class_="stat-value"), ui.tags.span("NUMÉRICAS", class_="stat-label"), class_="stat-card"),
                ui.div(ui.tags.span(str(len(cat_cols)), class_="stat-value"), ui.tags.span("CATEGÓRICAS", class_="stat-label"), class_="stat-card"),
                ui.div(ui.tags.span(f"{miss_pct}%", class_="stat-value"), ui.tags.span("DATOS FALTANTES", class_="stat-label"), class_="stat-card"),
                class_="stats-grid"
            ),

            # Missing bars
            ui.div(
                ui.div("VALORES FALTANTES POR COLUMNA", class_="card-title"),
                ui.HTML(f'<div class="missing-bar-wrap">{miss_bars}</div>'),
                class_="card"
            ),

            # Dtype table
            ui.div(
                ui.div("TIPOS DE COLUMNAS", class_="card-title"),
                ui.HTML(f"""
                <div class="df-table-wrap">
                  <table class="df-table">
                    <thead><tr><th>Columna</th><th>Tipo</th><th>Dtype</th><th>Únicos</th><th>Nulos</th></tr></thead>
                    <tbody>{dtype_rows}</tbody>
                  </table>
                </div>
                """),
                class_="card"
            ),

            # Preview
            ui.div(
                ui.div("PREVIEW DE DATOS", class_="card-title"),
                ui.HTML(df_preview_html(df)),
                class_="card"
            )
        )

    # ─────────────────────────────────────────────────────────────
    # EDA PAGE
    # ─────────────────────────────────────────────────────────────
    def render_eda(df):
        if df is None:
            return ui.div("Sin datos")

        num_cols = get_num_cols(df)
        cat_cols = get_cat_cols(df)
        num_default = num_cols[: min(6, len(num_cols))]
        cat_default = cat_cols[: min(6, len(cat_cols))]

        return ui.div(
            ui.div(ui.tags.h2("EDA", class_="section-title"), ui.p("Estadísticas, correlaciones y distribuciones interactivas", class_="section-sub")),
            ui.div(
                ui.div("CONFIGURAR ANÁLISIS", class_="card-title"),
                ui.div(
                    ui.div(ui.input_select("eda_corr_method", "Correlación", {"pearson": "Pearson", "spearman": "Spearman", "kendall": "Kendall"}), class_="ctrl-group"),
                    ui.div(ui.input_selectize("eda_num_cols", "Variables numéricas", {c: c for c in num_cols}, selected=num_default, multiple=True), class_="ctrl-group"),
                    ui.div(ui.input_selectize("eda_cat_cols", "Variables categóricas", {c: c for c in cat_cols}, selected=cat_default, multiple=True), class_="ctrl-group"),
                    ui.div(ui.input_select("eda_dist_col", "Variable para distribución", {c: c for c in num_cols}, selected=num_default[0] if num_default else None), class_="ctrl-group"),
                    ui.div(ui.input_select("eda_dist_kind", "Vista", {"hist": "Histograma", "hist_density": "Histograma + densidad", "box": "Boxplot"}), class_="ctrl-group"),
                    class_="ctrl-row"
                ),
                class_="card"
            ),
            ui.div(ui.output_ui("eda_summary"), class_="card"),
            ui.div(ui.output_ui("eda_corr_plot"), class_="card plot-card"),
            ui.div(ui.output_ui("eda_dist_plot"), class_="card plot-card")
        )

    @output
    @render.ui
    def eda_summary():
        df = df_current()
        if df is None:
            return ui.div()
        num_cols = input.eda_num_cols() or get_num_cols(df)
        cat_cols = input.eda_cat_cols() or get_cat_cols(df)
        if num_cols:
            corr_frame = df[num_cols].corr(numeric_only=True)
            avg_corr = round(float(corr_frame.abs().mean().mean()), 3) if len(num_cols) > 1 else 0
            summary = df[num_cols].describe().round(3)
            summary_rows = "".join(
                f"<tr><td>{idx}</td>" + "".join(f"<td class='num-cell'>{val}</td>" for val in row) + "</tr>"
                for idx, row in summary.iterrows()
            )
        else:
            avg_corr = 0
            summary_rows = "<tr><td colspan='100%'>No hay variables numéricas seleccionadas</td></tr>"
        return ui.HTML(f"""
        <div class='stats-grid'>
          <div class='stat-card'><span class='stat-value'>{len(num_cols)}</span><span class='stat-label'>Numéricas</span></div>
          <div class='stat-card'><span class='stat-value'>{len(cat_cols)}</span><span class='stat-label'>Categóricas</span></div>
          <div class='stat-card'><span class='stat-value'>{avg_corr}</span><span class='stat-label'>|Corr| media</span></div>
        </div>
        <div class='df-table-wrap'>
          <table class='df-table'>
            <thead><tr><th>Métrica</th>{''.join(f'<th>{c}</th>' for c in (df[num_cols].describe().round(3).columns if num_cols else []))}</tr></thead>
            <tbody>{summary_rows}</tbody>
          </table>
        </div>
        """)

    @output
    @render.ui
    def eda_corr_plot():
        df = df_current()
        if df is None:
            return ui.div()
        selected = input.eda_num_cols() or get_num_cols(df)
        selected = [col for col in selected if col in df.columns]
        if len(selected) < 2:
            return ui.div("Selecciona al menos dos variables numéricas para ver la correlación.")
        fig = make_corr_heatmap(df, selected, input.eda_corr_method())
        return ui.div(ui.tags.h3("Matriz de correlación", class_="card-title"), html_figure(fig, height=520))

    @output
    @render.ui
    def eda_dist_plot():
        df = df_current()
        if df is None:
            return ui.div()
        column = input.eda_dist_col()
        if not column or column not in df.columns:
            return ui.div("Selecciona una variable numérica para ver su distribución.")
        fig = make_distribution_figure(df, column, input.eda_dist_kind())
        return ui.div(ui.tags.h3("Distribuciones iniciales", class_="card-title"), html_figure(fig, height=460))

    # ─────────────────────────────────────────────────────────────
    # DOCUMENTATION PAGE
    # ─────────────────────────────────────────────────────────────
    def render_docs(df):
        return ui.div(
            ui.div(ui.tags.h2("Documentación", class_="section-title"), ui.p("Criterios metodológicos del sprint uno", class_="section-sub")),
            ui.div(
                ui.HTML("""
                <div class='doc-panel'>
                  <h3>Carga de datos</h3>
                  <p>La carga admite separadores coma, punto y coma, tab y un separador personalizado. El parser intenta el encoding configurado y hace fallback a UTF-8 y Latin-1.</p>
                </div>
                <div class='doc-panel'>
                  <h3>Valores faltantes</h3>
                  <p>Se clasifican por porcentaje relativo para priorizar limpieza: Trivial, Manejable, Sofisticado y Perjudicial.</p>
                </div>
                <div class='doc-panel'>
                  <h3>Outliers</h3>
                  <p>La detección soporta IQR y Z-score. La vista resume conteos por variable y clasifica severidad por porcentaje de atípicos.</p>
                </div>
                <div class='doc-panel'>
                  <h3>EDA</h3>
                  <p>El panel de análisis explora estadísticas descriptivas, matrices de correlación y distribuciones con Plotly para variables seleccionadas.</p>
                </div>
                """),
                class_="card"
            )
        )

    # ─────────────────────────────────────────────────────────────
    # MISSING VALUES PAGE
    # ─────────────────────────────────────────────────────────────
    def render_missing(df):
        if df is None:
            return ui.div("Sin datos")

        cols_with_null = df.columns[df.isnull().any()].tolist()
        num_cols = get_num_cols(df)
        cat_cols = get_cat_cols(df)

        if not cols_with_null:
            return ui.div(
                ui.div(ui.tags.h2("Valores Faltantes", class_="section-title"),
                       ui.p("Imputación y eliminación de NaN", class_="section-sub")),
                ui.div(ui.HTML('<span style="color:var(--accent);font-size:1.2rem;">✓</span> No hay valores faltantes en el dataset actual.'),
                       class_="card")
            )

        col_options = {"_all_": "— Todas con nulos —"} | {c: f"{c} ({df[c].isnull().sum()} nulos)" for c in cols_with_null}
        strat_num = {"mean": "Media", "median": "Mediana", "mode": "Moda", "constant": "Constante", "drop_rows": "Eliminar filas", "drop_col": "Eliminar columna"}
        strat_cat = {"mode": "Moda", "constant": "Constante (unknown)", "drop_rows": "Eliminar filas", "drop_col": "Eliminar columna"}

        return ui.div(
            ui.div(ui.tags.h2("Valores Faltantes", class_="section-title"),
                   ui.p("Imputación y eliminación de NaN", class_="section-sub")),

            ui.div(
                ui.div("CONFIGURAR IMPUTACIÓN", class_="card-title"),
                ui.div(
                    ui.div(
                        ui.input_select("miss_col", "Columna:", col_options),
                        class_="ctrl-group"
                    ),
                    ui.div(
                        ui.input_select("miss_strat_num", "Estrategia (numéricas):", strat_num),
                        class_="ctrl-group"
                    ),
                    ui.div(
                        ui.input_select("miss_strat_cat", "Estrategia (categóricas):", strat_cat),
                        class_="ctrl-group"
                    ),
                    ui.div(
                        ui.input_text("miss_constant", "Valor constante (si aplica):", value="0"),
                        class_="ctrl-group"
                    ),
                    class_="ctrl-row"
                ),
                ui.input_action_button("apply_missing", "Aplicar imputación", class_="btn btn-primary"),
                ui.tags.span(" "),
                ui.input_action_button("reset_missing", "Resetear columna", class_="btn btn-danger"),
                class_="card"
            ),

            ui.div(
                ui.div(
                    ui.input_action_button("jump_docs", "!", class_="info-icon"),
                    ui.tags.span("ESTADO ACTUAL DE NULOS", style="margin-left:8px;"),
                    class_="card-title"
                ),
                ui.output_ui("missing_status"),
                class_="card"
            ),

            ui.div(
                ui.div("PREVIEW", class_="card-title"),
                ui.HTML(df_preview_html(df)),
                class_="card"
            )
        )

    @output
    @render.ui
    def missing_status():
        df = df_current()
        if df is None:
            return ui.div()
        report = missing_report_html(df)
        if df.isnull().sum().sum() == 0:
            return ui.HTML('<span style="color:var(--accent)">✓ Sin valores faltantes</span>')
        return ui.HTML(report)

    @reactive.Effect
    @reactive.event(input.jump_docs)
    def _jump_docs_from_missing():
        current_page.set("docs")

    @reactive.Effect
    @reactive.event(input.apply_missing)
    def _apply_missing():
        df = df_current().copy()
        col_sel = input.miss_col()
        strat_num = input.miss_strat_num()
        strat_cat = input.miss_strat_cat()
        const_val = input.miss_constant()
        num_cols = get_num_cols(df)
        cat_cols = get_cat_cols(df)

        def impute_col(df, col):
            dtype = "num" if col in num_cols else "cat"
            strat = strat_num if dtype == "num" else strat_cat
            n_before = df[col].isnull().sum()
            if n_before == 0:
                return df
            if strat == "mean":
                df[col].fillna(df[col].mean(), inplace=True)
            elif strat == "median":
                df[col].fillna(df[col].median(), inplace=True)
            elif strat == "mode":
                df[col].fillna(df[col].mode()[0], inplace=True)
            elif strat == "constant":
                fill_val = float(const_val) if dtype == "num" else (const_val or "unknown")
                df[col].fillna(fill_val, inplace=True)
            elif strat == "drop_rows":
                df.dropna(subset=[col], inplace=True)
            elif strat == "drop_col":
                df.drop(columns=[col], inplace=True)
            return df

        if col_sel == "_all_":
            for col in df.columns[df.isnull().any()].tolist():
                df = impute_col(df, col)
            add_log(f"Imputación aplicada a todas las columnas con nulos")
        else:
            df = impute_col(df, col_sel)
            add_log(f"Imputación aplicada a '{col_sel}'")

        df_current.set(df)

    # ─────────────────────────────────────────────────────────────
    # ENCODING PAGE
    # ─────────────────────────────────────────────────────────────
    def render_encode(df):
        if df is None:
            return ui.div("Sin datos")
        cat_cols = get_cat_cols(df)
        if not cat_cols:
            return ui.div(
                ui.div(ui.tags.h2("Encoding", class_="section-title"),
                       ui.p("Codificación de variables categóricas", class_="section-sub")),
                ui.div("No hay columnas categóricas disponibles.", class_="card")
            )

        col_opts = {c: f"{c} ({df[c].nunique()} únicos)" for c in cat_cols}

        return ui.div(
            ui.div(ui.tags.h2("Encoding", class_="section-title"),
                   ui.p("Codificación de variables categóricas", class_="section-sub")),

            ui.div(
                ui.div("CONFIGURAR ENCODING", class_="card-title"),
                ui.div(
                    ui.div(ui.input_select("enc_col", "Columna:", {**{"_all_": "— Todas categóricas —"}, **col_opts}), class_="ctrl-group"),
                    ui.div(ui.input_select("enc_method", "Método:", {
                        "label": "Label Encoding",
                        "onehot": "One-Hot Encoding",
                        "ordinal": "Ordinal (manual no disp.)",
                        "binary": "Binary (0/1 si 2 únicos)",
                    }), class_="ctrl-group"),
                    class_="ctrl-row"
                ),
                ui.input_action_button("apply_encode", "Aplicar encoding", class_="btn btn-primary"),
                class_="card"
            ),

            ui.div(
                ui.div("COLUMNAS CATEGÓRICAS ACTUALES", class_="card-title"),
                ui.output_ui("encode_status"),
                class_="card"
            ),

            ui.div(
                ui.div("PREVIEW", class_="card-title"),
                ui.HTML(df_preview_html(df)),
                class_="card"
            )
        )

    @output
    @render.ui
    def encode_status():
        df = df_current()
        if df is None:
            return ui.div()
        cat_cols = get_cat_cols(df)
        if not cat_cols:
            return ui.HTML('<span style="color:var(--accent)">✓ Sin columnas categóricas</span>')
        rows = "".join(
            f"<tr><td>{c}</td><td>{df[c].nunique()}</td><td>{', '.join(str(v) for v in df[c].unique()[:5])}{'...' if df[c].nunique() > 5 else ''}</td></tr>"
            for c in cat_cols
        )
        return ui.HTML(f"""
        <div class="df-table-wrap">
          <table class="df-table">
            <thead><tr><th>Columna</th><th>Únicos</th><th>Valores</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """)

    @reactive.Effect
    @reactive.event(input.apply_encode)
    def _apply_encode():
        df = df_current().copy()
        method = input.enc_method()
        col_sel = input.enc_col()
        cat_cols = get_cat_cols(df)
        cols = cat_cols if col_sel == "_all_" else [col_sel]

        for col in cols:
            if col not in df.columns:
                continue
            if method == "label":
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                add_log(f"Label encoding: '{col}'")
            elif method == "onehot":
                dummies = pd.get_dummies(df[col], prefix=col, drop_first=False).astype(int)
                df = pd.concat([df.drop(columns=[col]), dummies], axis=1)
                add_log(f"One-Hot encoding: '{col}' → {dummies.shape[1]} cols")
            elif method == "binary":
                if df[col].nunique() == 2:
                    vals = df[col].unique()
                    df[col] = df[col].map({vals[0]: 0, vals[1]: 1})
                    add_log(f"Binary encoding: '{col}'")
                else:
                    add_log(f"Binary encoding: '{col}' tiene {df[col].nunique()} únicos (se necesitan exactamente 2)")

        df_current.set(df)

    # ─────────────────────────────────────────────────────────────
    # SCALING PAGE
    # ─────────────────────────────────────────────────────────────
    def render_scale(df):
        if df is None:
            return ui.div("Sin datos")
        num_cols = get_num_cols(df)
        if not num_cols:
            return ui.div(
                ui.div(ui.tags.h2("Scaling", class_="section-title"),
                       ui.p("Normalización y estandarización de variables numéricas", class_="section-sub")),
                ui.div("No hay columnas numéricas.", class_="card")
            )

        col_opts = {c: c for c in num_cols}

        return ui.div(
            ui.div(ui.tags.h2("Scaling", class_="section-title"),
                   ui.p("Normalización y estandarización de variables numéricas", class_="section-sub")),

            ui.div(
                ui.div("CONFIGURAR SCALING", class_="card-title"),
                ui.div(
                    ui.div(ui.input_select("scale_col", "Columna:", {**{"_all_": "— Todas numéricas —"}, **col_opts}), class_="ctrl-group"),
                    ui.div(ui.input_select("scale_method", "Método:", {
                        "standard": "StandardScaler (Z-score)",
                        "minmax": "MinMaxScaler [0,1]",
                        "robust": "RobustScaler (IQR)",
                        "log": "Log Transform (log1p)",
                        "sqrt": "Raíz Cuadrada",
                    }), class_="ctrl-group"),
                    class_="ctrl-row"
                ),
                ui.input_action_button("apply_scale", "Aplicar scaling", class_="btn btn-primary"),
                class_="card"
            ),

            ui.div(
                ui.div("ESTADÍSTICAS ACTUALES", class_="card-title"),
                ui.output_ui("scale_stats"),
                class_="card"
            ),

            ui.div(
                ui.div("PREVIEW", class_="card-title"),
                ui.HTML(df_preview_html(df)),
                class_="card"
            )
        )

    @output
    @render.ui
    def scale_stats():
        df = df_current()
        if df is None:
            return ui.div()
        num_cols = get_num_cols(df)
        desc = df[num_cols].describe().round(3)
        rows = ""
        for col in num_cols:
            rows += f"""<tr>
              <td>{col}</td>
              <td class="num-cell">{desc.loc['mean', col]}</td>
              <td class="num-cell">{desc.loc['std', col]}</td>
              <td class="num-cell">{desc.loc['min', col]}</td>
              <td class="num-cell">{desc.loc['max', col]}</td>
            </tr>"""
        return ui.HTML(f"""
        <div class="df-table-wrap">
          <table class="df-table">
            <thead><tr><th>Columna</th><th>Media</th><th>Std</th><th>Min</th><th>Max</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """)

    @reactive.Effect
    @reactive.event(input.apply_scale)
    def _apply_scale():
        df = df_current().copy()
        method = input.scale_method()
        col_sel = input.scale_col()
        num_cols = get_num_cols(df)
        cols = num_cols if col_sel == "_all_" else [col_sel]
        cols = [c for c in cols if c in df.columns]

        if method == "standard":
            scaler = StandardScaler()
            df[cols] = scaler.fit_transform(df[cols])
            add_log(f"StandardScaler aplicado a: {cols}")
        elif method == "minmax":
            scaler = MinMaxScaler()
            df[cols] = scaler.fit_transform(df[cols])
            add_log(f"MinMaxScaler aplicado a: {cols}")
        elif method == "robust":
            scaler = RobustScaler()
            df[cols] = scaler.fit_transform(df[cols])
            add_log(f"RobustScaler aplicado a: {cols}")
        elif method == "log":
            for c in cols:
                df[c] = np.log1p(df[c].clip(lower=0))
            add_log(f"Log1p transform aplicado a: {cols}")
        elif method == "sqrt":
            for c in cols:
                df[c] = np.sqrt(df[c].clip(lower=0))
            add_log(f"Sqrt transform aplicado a: {cols}")

        df_current.set(df)

    # ─────────────────────────────────────────────────────────────
    # OUTLIERS PAGE
    # ─────────────────────────────────────────────────────────────
    def render_outlier(df):
        if df is None:
            return ui.div("Sin datos")
        num_cols = get_num_cols(df)
        if not num_cols:
            return ui.div(
                ui.div(ui.tags.h2("Outliers", class_="section-title"),
                       ui.p("Detección y tratamiento de valores atípicos", class_="section-sub")),
                ui.div("No hay columnas numéricas.", class_="card")
            )

        col_opts = {c: c for c in num_cols}
        method_default = input.out_method() if hasattr(input, "out_method") else "iqr"

        out_rows = ""
        for col in num_cols:
            series = df[col].dropna()
            if series.empty:
                continue
            if method_default == "zscore":
                mean = series.mean()
                std = series.std(ddof=0) or 1
                n_out = (np.abs(series - mean) > (input.out_threshold() if hasattr(input, "out_threshold") else 3.0) * std).sum()
                low_label = f"±{round((input.out_threshold() if hasattr(input, 'out_threshold') else 3.0), 2)}σ"
                high_label = "Z-score"
            else:
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                n_out = ((series < Q1 - 1.5 * IQR) | (series > Q3 + 1.5 * IQR)).sum()
                low_label = round(Q1, 2)
                high_label = round(Q3, 2)
            pct = round(100 * n_out / len(series), 1)
            category, color = outlier_category_for_pct(pct)
            out_rows += f"<tr><td>{col}</td><td style='color:{color}'>{n_out}</td><td>{pct}%</td><td><span class='pill' style='background:{color};color:#fff'>{category}</span></td><td class='num-cell'>{low_label}</td><td class='num-cell'>{high_label}</td></tr>"

        return ui.div(
            ui.div(ui.tags.h2("Outliers", class_="section-title"),
                   ui.p("Detección y tratamiento de valores atípicos", class_="section-sub")),

            ui.div(
                ui.div("DETECCIÓN Y CONFIGURACIÓN", class_="card-title"),
                ui.div(
                    ui.div(ui.input_select("out_method", "Método", {"iqr": "IQR", "zscore": "Z-score"}, selected="iqr"), class_="ctrl-group"),
                    ui.div(ui.input_numeric("out_threshold", "Umbral Z-score", value=3.0, min=0.5, max=6.0, step=0.1), class_="ctrl-group"),
                    ui.div(ui.input_selectize("out_cols_view", "Variables a graficar", {c: c for c in num_cols}, selected=num_cols[: min(6, len(num_cols))], multiple=True), class_="ctrl-group"),
                    class_="ctrl-row"
                ),
                ui.div("RESUMEN DE OUTLIERS", class_="card-title"),
                ui.HTML(f"""
                <div class="df-table-wrap">
                  <table class="df-table">
                    <thead><tr><th>Columna</th><th>Outliers</th><th>%</th><th>Categoría</th><th>Lower</th><th>Upper</th></tr></thead>
                    <tbody>{out_rows}</tbody>
                  </table>
                </div>
                """),
                class_="card"
            ),

            ui.div(
                ui.div("BOXPLOTS", class_="card-title"),
                ui.output_ui("outlier_plot"),
                class_="card plot-card"
            ),

            ui.div(
                ui.div("TRATAMIENTO", class_="card-title"),
                ui.div(
                    ui.div(ui.input_select("out_col", "Columna:", {**{"_all_": "— Todas numéricas —"}, **col_opts}), class_="ctrl-group"),
                    ui.div(ui.input_select("out_method", "Método:", {
                        "iqr_clip": "IQR Clipping (Winsorize)",
                        "iqr_drop": "IQR Drop rows",
                        "zscore_clip": "Z-score Clipping (±3σ)",
                        "zscore_drop": "Z-score Drop rows",
                        "cap_pct": "Cap Percentil 1%-99%",
                    }), class_="ctrl-group"),
                    class_="ctrl-row"
                ),
                ui.input_action_button("apply_outlier", "Aplicar tratamiento", class_="btn btn-primary"),
                class_="card"
            )
        )

    @reactive.Effect
    @reactive.event(input.apply_outlier)
    def _apply_outlier():
        df = df_current().copy()
        method = input.out_method()
        threshold = float(input.out_threshold() or 3.0)
        col_sel = input.out_col()
        num_cols = get_num_cols(df)
        cols = num_cols if col_sel == "_all_" else [col_sel]
        cols = [c for c in cols if c in df.columns]
        rows_before = len(df)

        for col in cols:
            if method == "iqr_clip":
                Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
                IQR = Q3 - Q1
                df[col] = df[col].clip(Q1 - 1.5*IQR, Q3 + 1.5*IQR)
            elif method == "iqr_drop":
                Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
                IQR = Q3 - Q1
                df = df[(df[col] >= Q1 - 1.5*IQR) & (df[col] <= Q3 + 1.5*IQR)]
            elif method == "zscore_clip":
                mean, std = df[col].mean(), df[col].std()
                df[col] = df[col].clip(mean - threshold*std, mean + threshold*std)
            elif method == "zscore_drop":
                mean, std = df[col].mean(), df[col].std()
                df = df[np.abs(df[col] - mean) <= threshold*std]
            elif method == "cap_pct":
                lo, hi = df[col].quantile(0.01), df[col].quantile(0.99)
                df[col] = df[col].clip(lo, hi)

        rows_after = len(df)
        add_log(f"Outliers tratados en {cols}: {method} ({rows_before - rows_after} filas eliminadas)")
        df_current.set(df)

    @output
    @render.ui
    def outlier_plot():
        df = df_current()
        if df is None:
            return ui.div()
        selected = input.out_cols_view() if hasattr(input, "out_cols_view") and input.out_cols_view() else get_num_cols(df)
        selected = [col for col in selected if col in df.columns]
        if not selected:
            return ui.div("Selecciona al menos una variable numérica para ver los boxplots.")
        fig = go.Figure()
        for col in selected:
            fig.add_trace(go.Box(y=df[col], name=col, boxmean=True))
        fig.update_layout(title="Boxplots de variables numéricas")
        return html_figure(fig, height=500)

    # ─────────────────────────────────────────────────────────────
    # DROP COLUMNS PAGE
    # ─────────────────────────────────────────────────────────────
    def render_drop(df):
        if df is None:
            return ui.div("Sin datos")

        col_checkboxes = ui.div(
            *[ui.div(
                ui.input_checkbox(f"drop_{col.replace(' ','_')}", col, value=False),
                class_="check-item"
              ) for col in df.columns],
            class_="check-list"
        )

        return ui.div(
            ui.div(ui.tags.h2("Drop Columns", class_="section-title"),
                   ui.p("Eliminar columnas innecesarias del dataset", class_="section-sub")),

            ui.div(
                ui.div("SELECCIONAR COLUMNAS A ELIMINAR", class_="card-title"),
                col_checkboxes,
                ui.tags.br(),
                ui.input_action_button("apply_drop", "Eliminar columnas seleccionadas", class_="btn btn-danger"),
                ui.tags.span(" "),
                ui.input_action_button("reset_df", "Reset completo al original", class_="btn btn-secondary"),
                class_="card"
            ),

            ui.div(
                ui.div("COLUMNAS ACTUALES", class_="card-title"),
                ui.HTML("".join(
                    f'<span class="pill {"pill-num" if c in get_num_cols(df) else "pill-cat"}">{c}</span>'
                    for c in df.columns
                )),
                class_="card"
            )
        )

    @reactive.Effect
    @reactive.event(input.apply_drop)
    def _apply_drop():
        df = df_current().copy()
        to_drop = []
        for col in df.columns:
            key = f"drop_{col.replace(' ','_')}"
            try:
                if input[key]():
                    to_drop.append(col)
            except:
                pass
        if to_drop:
            df.drop(columns=to_drop, inplace=True)
            add_log(f"Columnas eliminadas: {to_drop}")
            df_current.set(df)

    @reactive.Effect
    @reactive.event(input.reset_df)
    def _reset_df():
        df_current.set(df_original().copy())
        ops_log.set(["Dataset reseteado al original"])

    # ─────────────────────────────────────────────────────────────
    # EXPORT PAGE
    # ─────────────────────────────────────────────────────────────
    def render_export(df):
        if df is None:
            return ui.div("Sin datos")
        n_rows, n_cols = df.shape
        orig = df_original()
        orig_rows = orig.shape[0] if orig is not None else "?"
        orig_cols = orig.shape[1] if orig is not None else "?"

        ops = ops_log()
        log_html = "".join(f'<div class="log-line">{op}</div>' for op in ops)

        return ui.div(
            ui.div(ui.tags.h2("Export", class_="section-title"),
                   ui.p("Descargar el dataset preprocesado", class_="section-sub")),

            # Comparison
            ui.div(
                ui.div("RESUMEN DE TRANSFORMACIONES", class_="card-title"),
                ui.div(
                    ui.div(ui.tags.span(f"{orig_rows} → {n_rows}", class_="stat-value"), ui.tags.span("FILAS", class_="stat-label"), class_="stat-card"),
                    ui.div(ui.tags.span(f"{orig_cols} → {n_cols}", class_="stat-value"), ui.tags.span("COLUMNAS", class_="stat-label"), class_="stat-card"),
                    ui.div(ui.tags.span(str(df.isnull().sum().sum()), class_="stat-value"), ui.tags.span("NULOS RESTANTES", class_="stat-label"), class_="stat-card"),
                    ui.div(ui.tags.span(str(len(ops)), class_="stat-value"), ui.tags.span("OPERACIONES", class_="stat-label"), class_="stat-card"),
                    class_="stats-grid"
                ),
                class_="card"
            ),

            # Log
            ui.div(
                ui.div("LOG DE OPERACIONES", class_="card-title"),
                ui.HTML(f'<div class="log-box">{log_html if log_html else "<div class=log-line>Sin operaciones registradas</div>"}</div>'),
                class_="card"
            ),

            # Download
            ui.div(
                ui.tags.span("⬇", class_="download-icon"),
                ui.tags.p("Dataset listo para descargar", style="color:var(--muted);margin-bottom:12px;"),
                ui.download_button("download_csv", "Descargar CSV preprocesado"),
                class_="download-section"
            )
        )

    @output
    @render.download(filename="dataset_preprocesado.csv")
    def download_csv():
        df = df_current()
        if df is None:
            yield ""
            return
        yield df.to_csv(index=False)

    # ─────────────────────────────────────────────────────────────
    # MAIN CONTENT ROUTER
    # ─────────────────────────────────────────────────────────────
    @output
    @render.ui
    def main_content():
        page = current_page()
        df = df_current()
        if page == "overview":
            return render_overview(df)
        elif page == "eda":
            return render_eda(df)
        elif page == "missing":
            return render_missing(df)
        elif page == "encode":
            return render_encode(df)
        elif page == "scale":
            return render_scale(df)
        elif page == "outlier":
            return render_outlier(df)
        elif page == "drop":
            return render_drop(df)
        elif page == "export":
            return render_export(df)
        elif page == "docs":
            return render_docs(df)
        return ui.div("Página no encontrada")

    @output
    @render.ui
    def sidebar_nav():
        page = current_page()

        def nav_button(button_id, icon, label, page_name):
            is_active = page == page_name
            button_class = "nav-btn active" if is_active else "nav-btn"
            return ui.input_action_button(
                button_id,
                ui.HTML(f'<span class="nav-icon">{icon}</span> {label}'),
                class_=button_class,
            )

        return ui.div(
            nav_button("nav_overview", "📊", "Overview", "overview"),
            nav_button("nav_eda", "📈", "EDA", "eda"),
            nav_button("nav_missing", "🔍", "Missing Values", "missing"),
            nav_button("nav_encode", "🔢", "Encoding", "encode"),
            nav_button("nav_scale", "⚖️", "Scaling", "scale"),
            nav_button("nav_outlier", "🎯", "Outliers", "outlier"),
            nav_button("nav_drop", "🗑️", "Drop Columns", "drop"),
            nav_button("nav_export", "💾", "Export", "export"),
            nav_button("nav_docs", "📚", "Docs", "docs"),
        )

    # ─────────────────────────────────────────────────────────────
    # SIDEBAR STATUS
    # ─────────────────────────────────────────────────────────────
    @output
    @render.ui
    def sidebar_status():
        df = df_current()
        if df is None:
            return ui.div()
        n_miss = df.isnull().sum().sum()
        n_cat = len(get_cat_cols(df))
        accent_color = "var(--accent2)" if n_miss > 0 else "var(--accent)"
        sidebar_html = (
            '<div style="font-size:11px;color:var(--muted);line-height:2;">'
            f'<div>Rows <span style="color:var(--text)">{df.shape[0]} x {df.shape[1]}</span></div>'
            f'<div>Missing <span style="color:{accent_color}">{n_miss} nulos</span></div>'
            f'<div>Categorical <span style="color:var(--text)">{n_cat} cat cols</span></div>'
            f'<div>Ops <span style="color:var(--text)">{len(ops_log())} ops</span></div>'
            '</div>'
        )
        return ui.div(
            ui.HTML(sidebar_html)
        )

    # Handle second file upload widget
    @reactive.Effect
    @reactive.event(input.upload_csv2)
    def _handle_upload2():
        f = input.upload_csv2()
        if f:
            load_csv_file(f[0]["datapath"], f[0]["name"])

app = App(app_ui, server)