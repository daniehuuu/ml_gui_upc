"""Overview page"""
from html import escape
from base64 import urlsafe_b64encode, urlsafe_b64decode
from shiny import ui
from app_helpers import (
    df_preview_html as build_df_preview_html,
    get_num_cols,
    get_cat_cols,
    separator_options as DATA_SEPARATOR_OPTIONS,
)


def _col_token(col_name):
    return urlsafe_b64encode(str(col_name).encode("utf-8")).decode("ascii").rstrip("=")


def _col_from_token(token):
    padded = token + "=" * (-len(token) % 4)
    return urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")


def _normalize_dtype_name(dtype_name):
    return "int64" if str(dtype_name) == "Int64" else str(dtype_name)


def render_overview(df, load_config, dtype_manual_state):
    """Render the overview page"""
    if df is None:
        return ui.div(
            ui.div(ui.tags.h2("Dataset Overview", class_="section-title"), ui.p("Carga un dataset para empezar a trabajar", class_="section-sub")),
            ui.div(
                ui.tags.label("Carga configurable:", style="color:var(--muted);font-size:11px;display:block;margin-bottom:6px;"),
                ui.tags.button("Cargar archivo", type="button", onclick="openDatasetPicker('upload_csv2')", class_="btn btn-primary"),
                ui.div(
                    ui.div(ui.input_file("upload_csv2", "", accept=[".csv", ".tsv", ".txt"]), style="display:none"),
                    ui.div(ui.input_select("load_sep", "Separador", DATA_SEPARATOR_OPTIONS, selected=load_config()["separator"]), class_="ctrl-group"),
                    ui.div(ui.input_text("load_custom_sep", "Separador personalizado", value=load_config()["custom_separator"]), class_="ctrl-group"),
                    ui.div(ui.input_select("load_header", "Cabecera", {"infer": "Con cabecera", "none": "Sin cabecera"}, selected=load_config()["header"]), class_="ctrl-group"),
                    ui.div(ui.input_text("load_encoding", "Encoding", value=load_config()["encoding"]), class_="ctrl-group"),
                    class_="ctrl-row",
                ),
                ui.div(ui.tags.small("El botón de archivo abre el selector del sistema. La configuración se conserva durante la sesión."), style="color:var(--muted);"),
                class_="card",
            ),
            ui.div(
                ui.div("ESTADO", class_="card-title"),
                ui.div("No hay dataset cargado todavía. Usa el botón anterior para seleccionar un archivo.", style="color:var(--muted);"),
                class_="card",
            ),
        )

    n_rows, n_cols = df.shape
    num_cols = get_num_cols(df)
    cat_cols = get_cat_cols(df)
    total_missing = df.isnull().sum().sum()
    miss_pct = round(100 * total_missing / (n_rows * n_cols), 1)

    missing_per_col = df.isnull().sum()
    missing_per_col = missing_per_col[missing_per_col > 0].sort_values(ascending=False)
    miss_bars = ""
    for col, cnt in missing_per_col.items():
        pct = round(100 * cnt / n_rows, 1)
        miss_bars += f"""
        <div class="missing-bar-row">
          <span class="missing-bar-label">{escape(str(col))}</span>
          <div class="missing-bar"><div class="missing-bar-fill" style="width:{pct}%"></div></div>
          <span class="missing-pct">{pct}%</span>
        </div>
        """
    if not miss_bars:
        miss_bars = '<span style="color:var(--accent)">✓ Sin valores faltantes</span>'

    dtype_rows = ""
    manual_state = dtype_manual_state()
    for col in df.columns:
        dtype = str(df[col].dtype)
        dtype_ui = _normalize_dtype_name(dtype)
        n_unique = df[col].nunique()
        n_null = df[col].isnull().sum()
        kind = "pill-num" if col in num_cols else "pill-cat"
        kind_label = "num" if col in num_cols else "cat"
        col_token = _col_token(col)
        changed = col in manual_state
        highlight_class = " dtype-cell-modified" if changed else ""

        reset_btn = ""
        if changed:
            reset_btn = (
                f"<button type='button' class='dtype-reset-btn' title='Revertir dtype' "
                f"onclick=\"Shiny.setInputValue('dtype_reset', {{token: '{col_token}', nonce: Date.now()}}, {{priority: 'event'}}); return false;\">x</button>"
            )

        options_html = "".join(
            (
                f"<button type='button' class='dtype-opt-btn{' active' if dtype_ui == opt else ''}' "
                f"onclick=\"Shiny.setInputValue('dtype_change', {{token: '{col_token}', dtype: '{opt}', nonce: Date.now()}}, {{priority: 'event'}}); return false;\">{opt}</button>"
            )
            for opt in ["int64", "float64", "object", "datetime64[ns]"]
        )

        dtype_rows += f"""
        <tr class='{"dtype-row-modified" if changed else ""}'>
          <td>{escape(str(col))}</td>
          <td><span class="pill {kind}">{kind_label}</span></td>
          <td class='dtype-cell{highlight_class}'>
            <div class='dtype-cell-head'>
              <details class='dtype-picker'>
                <summary class='dtype-current'>{escape(dtype_ui)}</summary>
                <div class='dtype-options'>{options_html}</div>
              </details>
              {reset_btn}
            </div>
          </td>
          <td>{n_unique}</td>
          <td>{'<span style="color:var(--accent2)">' + str(n_null) + '</span>' if n_null > 0 else n_null}</td>
        </tr>
        """

    return ui.div(
        ui.div(ui.tags.h2("Dataset Overview", class_="section-title"), ui.p("Resumen general del dataset cargado", class_="section-sub")),
        ui.div(
            ui.tags.label("Carga configurable:", style="color:var(--muted);font-size:11px;display:block;margin-bottom:6px;"),
            ui.tags.button("Cargar archivo", type="button", onclick="openDatasetPicker('upload_csv2')", class_="btn btn-primary"),
            ui.div(
                ui.div(ui.input_file("upload_csv2", "", accept=[".csv", ".tsv", ".txt"]), style="display:none"),
                ui.div(ui.input_select("load_sep", "Separador", DATA_SEPARATOR_OPTIONS, selected=load_config()["separator"]), class_="ctrl-group"),
                ui.div(ui.input_text("load_custom_sep", "Separador personalizado", value=load_config()["custom_separator"]), class_="ctrl-group"),
                ui.div(ui.input_select("load_header", "Cabecera", {"infer": "Con cabecera", "none": "Sin cabecera"}, selected=load_config()["header"]), class_="ctrl-group"),
                ui.div(ui.input_text("load_encoding", "Encoding", value=load_config()["encoding"]), class_="ctrl-group"),
                class_="ctrl-row",
            ),
            ui.div(ui.tags.small("La configuración se aplica al momento de cargar el archivo y se conserva durante la sesión."), style="color:var(--muted);"),
            class_="card",
            style="margin-bottom:16px;",
        ),
        ui.div(
            ui.div(ui.tags.span(str(n_rows), class_="stat-value"), ui.tags.span("FILAS", class_="stat-label"), class_="stat-card"),
            ui.div(ui.tags.span(str(n_cols), class_="stat-value"), ui.tags.span("COLUMNAS", class_="stat-label"), class_="stat-card"),
            ui.div(ui.tags.span(str(len(num_cols)), class_="stat-value"), ui.tags.span("NUMÉRICAS", class_="stat-label"), class_="stat-card"),
            ui.div(ui.tags.span(str(len(cat_cols)), class_="stat-value"), ui.tags.span("CATEGÓRICAS", class_="stat-label"), class_="stat-card"),
            ui.div(ui.tags.span(f"{miss_pct}%", class_="stat-value"), ui.tags.span("DATOS FALTANTES", class_="stat-label"), class_="stat-card"),
            class_="stats-grid",
        ),
        ui.div(
            ui.div("VALORES FALTANTES POR COLUMNA", class_="card-title"),
            ui.HTML(f'<div class="missing-bar-wrap">{miss_bars}</div>'),
            class_="card",
        ),
        ui.div(
            ui.div("TIPOS DE COLUMNAS", class_="card-title"),
            ui.HTML(f"""
            <div class="df-table-wrap">
              <table class="df-table">
                <thead><tr><th>Columna</th><th>Tipo</th><th>Dtype</th><th>Unicos</th><th>Nulos</th></tr></thead>
                <tbody>{dtype_rows}</tbody>
              </table>
            </div>
            """),
            class_="card",
        ),
        ui.div(
            ui.div("PREVIEW DE DATOS", class_="card-title"),
            ui.HTML(build_df_preview_html(df)),
            class_="card",
        ),
    )
