from pathlib import Path
from html import escape
from base64 import urlsafe_b64encode, urlsafe_b64decode
import time

from shiny import App, ui, render, reactive
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

from app_assets import CUSTOM_CSS as APP_CUSTOM_CSS, OPEN_DATASET_PICKER_JS
from app_helpers import read_csv_dataset, get_num_cols, get_cat_cols
from app_navigation import sidebar_nav_ui

# Import page modules
from pages import (
    render_overview,
    render_eda,
    register_eda_handlers,
    render_missing,
    register_missing_handlers,
    render_encode,
    register_encode_handlers,
    render_scale,
    register_scale_handlers,
    render_outlier,
    register_outlier_handlers,
    render_drop,
    register_drop_handlers,
    render_export,
    register_export_handlers,
    render_model,
    register_model_handlers,
    render_docs,
)

# ─── UI ────────────────────────────────────────────────────────────────────
app_ui = ui.page_fluid(
    ui.tags.style(APP_CUSTOM_CSS),
    ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),
    ui.tags.script(src="https://cdn.plot.ly/plotly-2.32.0.min.js"),

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

            ui.tags.script(OPEN_DATASET_PICKER_JS),

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
    ),

    ui.output_ui("toast_notification")
)

# ─── Server ────────────────────────────────────────────────────────────────
def server(input, output, session):

    # ── State Management
    current_page = reactive.Value("overview")
    df_original = reactive.Value(None)
    df_current = reactive.Value(None)
    encoding_state = reactive.Value({})
    ops_log = reactive.Value([])
    dtype_manual_state = reactive.Value({})
    toast_state = reactive.Value(None)
    load_config = reactive.Value({"separator": ";", "custom_separator": "|", "header": "infer", "encoding": "utf-8"})

    # ── Helper Functions
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
        df, trial_encoding, last_error = read_csv_dataset(file_path, separator, header, encoding)
        if df is None:
            return None, f"No fue posible leer el archivo con separador {separator!r}. Error: {last_error}"

        load_config.set({
            "separator": separator,
            "custom_separator": input.load_custom_sep() if hasattr(input, "load_custom_sep") else "",
            "header": "infer" if header == 0 else "none",
            "encoding": trial_encoding,
        })
        df_original.set(df.copy())
        df_current.set(df.copy())
        dtype_manual_state.set({})
        ops_log.set([
            f"Dataset cargado: {file_name or Path(file_path).name} ({df.shape[0]} filas × {df.shape[1]} cols)",
            f"Separador: {separator!r} | cabecera: {'inferida' if header == 0 else 'sin cabecera'} | encoding: {trial_encoding}",
        ])
        return df, None

    def add_log(msg):
        ops_log.set(ops_log() + [msg])

    def push_toast(message, level="info"):
        toast_state.set({
            "id": time.time_ns(),
            "message": str(message),
            "level": level,
        })

    def _col_token(col_name):
        return urlsafe_b64encode(str(col_name).encode("utf-8")).decode("ascii").rstrip("=")

    def _col_from_token(token):
        padded = token + "=" * (-len(token) % 4)
        return urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")

    def _normalize_dtype_name(dtype_name):
        return "int64" if str(dtype_name) == "Int64" else str(dtype_name)

    def _to_numeric_flexible(series):
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            cleaned = series.astype("string").str.strip()
            cleaned = cleaned.str.replace(",", ".", regex=False)
            cleaned = cleaned.replace({"": pd.NA, "None": pd.NA, "nan": pd.NA, "NaN": pd.NA})
            return pd.to_numeric(cleaned, errors="coerce")
        return pd.to_numeric(series, errors="coerce")

    def _convert_column_dtype(series, target_dtype):
        target_dtype = str(target_dtype)
        if target_dtype == "object":
            return series.astype("object"), None

        if target_dtype == "datetime64[ns]":
            try:
                converted = pd.to_datetime(series, errors="coerce")
                n_failed = series.notna().sum() - converted.notna().sum()
                if n_failed > 0:
                    sample_values = ", ".join(series[series.notna() & converted.isna()].astype(str).unique()[:3])
                    return None, f"No se pudieron convertir {n_failed} valores a datetime. Ejemplos: {sample_values}"
                return converted, None
            except Exception as e:
                return None, f"Error al convertir a datetime: {str(e)}"

        numeric = _to_numeric_flexible(series)
        invalid_mask = series.notna() & numeric.isna()
        if invalid_mask.any():
            sample_values = ", ".join(series[invalid_mask].astype(str).unique()[:3])
            return None, f"Hay valores no numéricos: {sample_values}"

        if target_dtype == "float64":
            return numeric.astype("float64"), None

        if target_dtype == "int64":
            non_null_numeric = numeric.dropna()
            rounded = np.round(non_null_numeric)
            if not np.all(np.isclose(non_null_numeric, rounded)):
                return None, "La columna tiene valores decimales y no puede convertirse a int64"
            int_like = np.round(numeric)
            if int_like.isna().any():
                return int_like.astype("Int64"), None
            return int_like.astype("int64"), None

        return None, f"Dtype no soportado: {target_dtype}"

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

    # ── Navigation handlers
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
    @reactive.event(input.nav_model)
    def _(): current_page.set("model")

    @reactive.Effect
    @reactive.event(input.nav_export)
    def _(): current_page.set("export")

    @reactive.Effect
    @reactive.event(input.nav_docs)
    def _(): current_page.set("docs")

    # ── Upload handlers
    @reactive.Effect
    @reactive.event(input.upload_csv)
    def _handle_upload():
        f = input.upload_csv()
        if f:
            load_csv_file(f[0]["datapath"], f[0]["name"])

    @reactive.Effect
    @reactive.event(input.upload_csv2)
    def _handle_upload2():
        f = input.upload_csv2()
        if f:
            load_csv_file(f[0]["datapath"], f[0]["name"])

    @reactive.Effect
    def _auto_clear_toast():
        toast = toast_state()
        if not toast:
            return
        reactive.invalidate_later(3.2)
        latest = toast_state()
        if latest and latest.get("id") == toast.get("id"):
            toast_state.set(None)

    # ── Overview page: dtype change handlers
    @reactive.Effect
    @reactive.event(input.dtype_change)
    def _apply_dtype_change():
        payload = input.dtype_change()
        if not payload:
            return

        token = payload.get("token")
        target_dtype = payload.get("dtype")
        if not token or target_dtype not in {"int64", "float64", "object", "datetime64[ns]"}:
            return

        df = df_current()
        if df is None:
            return
        col = _col_from_token(token)
        if col not in df.columns:
            return

        converted, err = _convert_column_dtype(df[col], target_dtype)
        if err:
            add_log(f"Cambio de dtype cancelado en '{col}' -> {target_dtype}: {err}")
            push_toast(f"No se pudo convertir {col} a {target_dtype}: {err}", "error")
            return

        if converted is None:
            return

        current_dtype = str(df[col].dtype)
        new_dtype = str(converted.dtype)
        if _normalize_dtype_name(current_dtype) == _normalize_dtype_name(new_dtype):
            return

        df_next = df.copy()
        df_next[col] = converted

        state = dict(dtype_manual_state())
        if col not in state:
            state[col] = {
                "dtype": current_dtype,
                "series": df[col].copy(),
            }

        if col in state and _normalize_dtype_name(new_dtype) == _normalize_dtype_name(state[col]["dtype"]):
            state.pop(col, None)

        dtype_manual_state.set(state)
        df_current.set(df_next)
        add_log(f"Cambio de dtype en '{col}': {current_dtype} -> {new_dtype}")
        push_toast(f"Dtype actualizado: {col} -> {new_dtype}", "success")

    @reactive.Effect
    @reactive.event(input.dtype_reset)
    def _reset_dtype_column():
        payload = input.dtype_reset()
        if not payload:
            return

        token = payload.get("token")
        if not token:
            return

        df = df_current()
        if df is None:
            return
        col = _col_from_token(token)
        state = dict(dtype_manual_state())
        if col not in state or col not in df.columns:
            return

        original_series = state[col]["series"]
        df_next = df.copy()
        df_next[col] = original_series.reindex(df_next.index)

        dtype_manual_state.set({k: v for k, v in state.items() if k != col})
        df_current.set(df_next)
        add_log(f"Dtype restaurado en '{col}' al estado original")
        push_toast(f"Dtype restaurado en {col}", "info")

    # ── Register page handlers
    register_eda_handlers(input, output, df_current)
    register_missing_handlers(input, output, session, df_current, current_page, add_log)
    register_encode_handlers(input, output, df_current, add_log, encoding_state)
    register_scale_handlers(input, output, df_current, add_log)
    register_outlier_handlers(input, output, df_current, add_log)
    register_drop_handlers(input, output, df_current, df_original, dtype_manual_state, ops_log, add_log)
    register_model_handlers(input, output, df_current, add_log, encoding_state)
    register_export_handlers(input, output, df_current)

    # ─────────────────────────────────────────────────────────────
    # MAIN CONTENT ROUTER
    # ─────────────────────────────────────────────────────────────
    @output
    @render.ui
    def main_content():
        page = current_page()
        df = df_current()
        if page == "overview":
            return render_overview(df, load_config, dtype_manual_state)
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
        elif page == "model":
            return render_model(df)
        elif page == "export":
            return render_export(df, df_original, ops_log)
        elif page == "docs":
            return render_docs(df)
        return ui.div("Página no encontrada")

    @output
    @render.ui
    def sidebar_nav():
        page = current_page()
        return sidebar_nav_ui(page)

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
        return ui.div(ui.HTML(sidebar_html))

    @output
    @render.ui
    def toast_notification():
        toast = toast_state()
        if not toast:
            return ui.div()
        level = toast.get("level", "info")
        message = escape(toast.get("message", ""))
        level_class = {
            "success": "toast-success",
            "error": "toast-error",
            "info": "toast-info",
        }.get(level, "toast-info")
        icon = {
            "success": "fa-check",
            "error": "fa-xmark",
            "info": "fa-circle-info",
        }.get(level, "fa-circle-info")
        return ui.HTML(
            f"""
            <div class='toast-host'>
              <div class='toast-item {level_class}'>
                <i class='fa-solid {icon}'></i>
                <span>{message}</span>
              </div>
            </div>
            """
        )


app = App(app_ui, server)
