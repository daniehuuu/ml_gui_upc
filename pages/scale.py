"""Scaling page"""
import numpy as np
from shiny import ui, render, reactive
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from app_helpers import (
    df_preview_html as build_df_preview_html,
    get_num_cols,
)


def render_scale(df):
    """Render the scaling page"""
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
            ui.HTML(build_df_preview_html(df)),
            class_="card"
        )
    )


def register_scale_handlers(input, output, df_current, add_log):
    """Register scaling page handlers"""
    
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
