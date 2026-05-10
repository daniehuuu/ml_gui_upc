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
            ui.output_ui("scale_stats_original"),
            class_="card"
        ),

        ui.div(
            ui.div("ESTADÍSTICAS ESCALADAS", class_="card-title"),
            ui.output_ui("scale_stats_scaled"),
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

    # Función auxiliar interna para construir las tablas de stats
    def _build_stats_table(df, cols):
        if not cols:
            return "<div style='color: var(--muted); font-style: italic;'>No hay variables en esta categoría.</div>"
        
        desc = df[cols].describe().round(3)
        rows = ""
        for col in cols:
            mean_val = desc.loc['mean', col] if 'mean' in desc.index else 'NaN'
            std_val  = desc.loc['std', col]  if 'std'  in desc.index else 'NaN'
            min_val  = desc.loc['min', col]  if 'min'  in desc.index else 'NaN'
            max_val  = desc.loc['max', col]  if 'max'  in desc.index else 'NaN'
            
            rows += f"""<tr>
              <td>{col}</td>
              <td class="num-cell">{mean_val}</td>
              <td class="num-cell">{std_val}</td>
              <td class="num-cell">{min_val}</td>
              <td class="num-cell">{max_val}</td>
            </tr>"""
            
        return f"""
        <div class="df-table-wrap">
          <table class="df-table">
            <thead><tr><th>Columna</th><th>Media</th><th>Std</th><th>Min</th><th>Max</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """
    
    @output
    @render.ui
    def scale_stats_original():
        df = df_current()
        if df is None:
            return ui.div()
        num_cols = get_num_cols(df)
        # Filtramos las que NO han sido escaladas (no terminan en _scaled)
        raw_cols = [c for c in num_cols if not c.endswith('_scaled')]
        return ui.HTML(_build_stats_table(df, raw_cols))
    
    @output
    @render.ui
    def scale_stats_scaled():
        df = df_current()
        if df is None: return ui.div()
        num_cols = get_num_cols(df)
        # Filtramos SOLO las que YA fueron escaladas
        scaled_cols = [c for c in num_cols if c.endswith('_scaled')]
        return ui.HTML(_build_stats_table(df, scaled_cols))

    @reactive.Effect
    @reactive.event(input.apply_scale)
    def _apply_scale():
        df = df_current().copy()
        method = input.scale_method()
        col_sel = input.scale_col()
        num_cols = get_num_cols(df)

        # Reconstruimos la lista de columnas base válidas
        base_cols = set()
        for c in num_cols:
            if c.endswith('_scaled'): continue
            elif c.startswith('_'): base_cols.add(c[1:])
            else: base_cols.add(c)
            
        if not base_cols:
            ui.notification_show("No hay columnas numéricas para escalar.", type="warning")
            return

        cols_to_process = list(base_cols) if col_sel == "_all_" else [col_sel]

        try:
            for base_col in cols_to_process:
                source_col = f"_{base_col}" if f"_{base_col}" in df.columns else base_col
                new_col = f"{base_col}_scaled"
                
                # Extraemos la data como un DataFrame de 1 columna para scikit-learn
                data_to_scale = df[[source_col]]
                
                # 2. Aplicamos la matemática y creamos/sobreescribimos la versión _scaled
                if method == "standard":
                    df[new_col] = StandardScaler().fit_transform(data_to_scale)
                elif method == "minmax":
                    df[new_col] = MinMaxScaler().fit_transform(data_to_scale)
                elif method == "robust":
                    df[new_col] = RobustScaler().fit_transform(data_to_scale)
                elif method == "log":
                    df[new_col] = np.log1p(df[source_col].clip(lower=0))
                elif method == "sqrt":
                    df[new_col] = np.sqrt(df[source_col].clip(lower=0))
                
                # Primera vez que se escala se oculta la original
                if source_col == base_col:
                    df.rename(columns={base_col: f"_{base_col}"}, inplace=True)

            add_log(f"Scaling '{method}' aplicado a: {cols_to_process}")
            df_current.set(df)
            ui.notification_show(f"Escalado '{method}' aplicada exitosamente.", type="success")

        except ValueError as e:
            ui.notification_show(f"Error estadístico. Verifica valores nulos o infinitos. Detalle: {str(e)[:50]}", type="error")
        except Exception as e:
            ui.notification_show(f"Error inesperado: {str(e)[:50]}", type="error")