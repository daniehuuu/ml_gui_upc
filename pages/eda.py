"""EDA (Exploratory Data Analysis) page"""
from shiny import ui, render
from app_helpers import (
    make_corr_heatmap as build_corr_heatmap,
    make_distribution_figure as build_distribution_figure,
    html_figure as render_plotly_html,
    get_num_cols,
    get_cat_cols,
)


def render_eda(df):
    """Render the EDA page"""
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


def register_eda_handlers(input, output, df_current):
    """Register EDA page handlers"""
    
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
        fig = build_corr_heatmap(df, selected, input.eda_corr_method())
        return ui.div(ui.tags.h3("Matriz de correlación", class_="card-title"), render_plotly_html(fig, height=520))

    @output
    @render.ui
    def eda_dist_plot():
        df = df_current()
        if df is None:
            return ui.div()
        column = input.eda_dist_col()
        if not column or column not in df.columns:
            return ui.div("Selecciona una variable numérica para ver su distribución.")
        fig = build_distribution_figure(df, column, input.eda_dist_kind())
        return ui.div(ui.tags.h3("Distribuciones iniciales", class_="card-title"), render_plotly_html(fig, height=460))
