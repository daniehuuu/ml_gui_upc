"""Outliers page"""
import numpy as np
from shiny import ui, render, reactive
import plotly.graph_objects as go
from app_helpers import (
    html_figure as render_plotly_html,
    get_num_cols,
    outlier_category_for_pct,
)


def render_outlier(df):
    """Render the outliers page"""
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
    method_default = "iqr"

    out_rows = ""
    for col in num_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        n_out = ((series < Q1 - 1.5 * IQR) | (series > Q3 + 1.5 * IQR)).sum()
        pct = round(100 * n_out / len(series), 1)
        category, color = outlier_category_for_pct(pct)
        out_rows += f"<tr><td>{col}</td><td style='color:{color}'>{n_out}</td><td>{pct}%</td><td><span class='pill' style='background:{color};color:#fff'>{category}</span></td><td class='num-cell'>{round(Q1, 2)}</td><td class='num-cell'>{round(Q3, 2)}</td></tr>"

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
                ui.div(ui.input_select("out_method_treat", "Método:", {
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


def register_outlier_handlers(input, output, df_current, add_log):
    """Register outliers page handlers"""
    
    @reactive.Effect
    @reactive.event(input.apply_outlier)
    def _apply_outlier():
        df = df_current().copy()
        method = input.out_method_treat()
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
        return render_plotly_html(fig, height=500)
