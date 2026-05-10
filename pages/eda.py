"""EDA (Exploratory Data Analysis) page"""
from shiny import ui, render
from app_helpers import (
    make_corr_heatmap as build_corr_heatmap,
    make_distribution_figure as build_distribution_figure,
    make_numeric_distribution_figure,
    make_categorical_distribution_figure,
    shapiro_wilk_table_html,
    html_figure as render_plotly_html,
    get_num_cols,
    get_cat_cols,
    make_scatter_plot_figure,
    make_cov_heatmap,
    outlier_report_html
)


def render_eda(df):
    """Render the EDA page"""
    if df is None:
        return ui.div("Sin datos")

    num_cols = get_num_cols(df)
    cat_cols = get_cat_cols(df)
    max_recommended_col = 5
    num_default = num_cols[: min(3, max_recommended_col)]
    cat_default = cat_cols[: min(3, max_recommended_col)]

    return ui.div(
        ui.div(ui.tags.h2("EDA", class_="section-title"), ui.p("Estadísticas, correlaciones y distribuciones interactivas", class_="section-sub")),
        ui.div(
            ui.div("Estadísticas simples", class_="card-title"),
            ui.div("Numéricas", class_="card-title"),
            ui.output_ui("eda_numeric_stats"),  
            ui.div("Categóricas", class_="card-title"),
            ui.output_ui("eda_categorical_stats"),  
            class_="card"
        ),
        ui.div(
            ui.div("Distribuciones (análisis univariado)", class_="card-title"),
            ui.div("Numéricas", class_="card-title"),
            ui.output_ui("eda_numeric_distribution"),  
            ui.div("Categóricas", class_="card-title"),
            ui.output_ui("eda_categorical_distribution"),  
            ui.div("Test de Shapiro-Wilk", class_="card-title"),
            ui.p("Prueba de normalidad para variables numéricas continuas", class_="card-subtitle"),
            ui.output_ui("eda_shapiro_results"), 
            class_="card"
        ),    
        ui.div(
            ui.div(
                ui.div(ui.input_select("eda_dist_col", "Variable para distribución", {c: c for c in num_cols}, selected=num_default[0] if num_default else None), class_="ctrl-group"),
                ui.div(ui.input_select("eda_dist_kind", "Vista", {"hist": "Histograma", "hist_density": "Histograma + densidad", "box": "Boxplot"}), class_="ctrl-group"),
                class_="ctrl-row"
            ),
            ui.div(
                ui.div("Reporte de Outliers", class_="card-title"),
                ui.p("Detección de valores atípicos", class_="card-subtitle"),
                ui.output_ui("eda_global_outliers"), 
                ui.div("Distribuciones iniciales", class_="card-title"),
                ui.output_ui("eda_dist_plot"),
                class_="card plot-card"
            ),
            #ui.output_ui("eda_dist_plot"), class_="card plot-card",
        ),
        # ui.div(ui.output_ui("eda_summary"), class_="card"),
        ui.div(
            ui.div("Distribuciones (análisis bivariado)", class_="card-title"),
            ui.div(
                ui.div(ui.input_select("eda_corr_method", "Correlación", {"pearson": "Pearson", "spearman": "Spearman", "kendall": "Kendall"}), class_="ctrl-group"),
                ui.div(ui.input_selectize("eda_num_cols", "Variables numéricas", {c: c for c in num_cols}, selected=num_default, multiple=True), class_="ctrl-group"),
                ui.div(ui.input_selectize("eda_cat_cols", "Variables categóricas", {c: c for c in cat_cols}, selected=cat_default, multiple=True), class_="ctrl-group"),
                class_="ctrl-row"
            ),
            ui.div("Matriz de covarianza", class_="card-title"),
            ui.div(ui.output_ui("eda_cov_plot"), class_="card plot-card"),
            ui.div("Matriz de correlación", class_="card-title"),            
            ui.div(ui.output_ui("eda_corr_plot"), class_="card plot-card"),
            ui.div("Gráfico de correlación", class_="card-title"),
            ui.div(
                ui.div(ui.input_select("eda_bivar_x", "Variable X", {c: c for c in num_cols}, selected=num_cols[0] if len(num_cols) > 0 else None), class_="ctrl-group"),                
                ui.div(ui.input_select("eda_bivar_y", "Variable Y", {c: c for c in num_cols}, selected=num_cols[1] if len(num_cols) > 1 else num_cols[0] if num_cols else None), class_="ctrl-group"),        
                ui.div(ui.input_select("eda_bivar_color", "Agrupar por ", {"": "Ninguno"} | {c: c for c in cat_cols}, selected=""), class_="ctrl-group"),        
                class_="ctrl-row"
            ),
            ui.output_ui("eda_correlation_distribution"),
            class_="card"
        )
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
        selected = input.eda_num_cols()
        selected = [col for col in selected if col in df.columns]

        if len(selected) > 10:
            return ui.div(
                ui.tags.h3("Matriz de correlación", class_="card-title"),
                ui.p(
                    f"Has seleccionado {len(selected)} variables. Por favor, selecciona un máximo de 10 para mantener el rendimiento y la legibilidad del gráfico.", 
                    style="color: orange; font-weight: bold; padding: 10px;"
                )
            )
        
        if len(selected) < 2:
            return ui.div("Selecciona al menos dos variables numéricas para ver la correlación.")
        fig = build_corr_heatmap(df, selected, input.eda_corr_method())

        legend_corr = """
        <div style="margin-top: 16px; color: var(--muted); font-size: 12px; line-height: 1.6;">
          <strong>Leyenda de Correlación (Estandarizada):</strong><br>
          <strong>Rango:</strong> De -1 a 1. Mide la <em>fuerza</em> y <em>dirección</em> de la relación lineal.<br>
          <strong>Cercano a 1:</strong> Relación positiva fuerte (si una variable sube, la otra también).<br>
          <strong>Cercano a -1:</strong> Relación negativa fuerte (si una variable sube, la otra baja).<br>
          <strong>Cercano a 0:</strong> Ausencia de relación lineal (no tienen impacto directo entre sí).
        </div>
        """

        return ui.div(
            ui.tags.h3("Matriz de correlación", class_="card-title"), 
            render_plotly_html(fig, height=520),
            ui.HTML(legend_corr) # Añadimos la leyenda al final del contenedor
        )

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
        return ui.div(ui.tags.h3(input.eda_dist_kind(), class_="card-title"), render_plotly_html(fig, height=460))

    @output
    @render.ui
    def eda_numeric_stats():
        df = df_current()
        if df is None:
            return ui.div()
        
        num_cols = get_num_cols(df)
        
        if not num_cols:
            return ui.div("No hay variables numéricas seleccionadas.")
        
        # Calcular estadísticas para cada columna numérica
        stats_list = []
        for col in num_cols:
            series = df[col]
            stats_list.append({
                'Variable': col,
                'Media': series.mean(),
                'Q1': series.quantile(0.25),
                'Mediana': series.median(),
                'Q3': series.quantile(0.75),
                'Min': series.min(),
                'Max': series.max(),
                'Rango': series.max() - series.min(),
                'IQR': series.quantile(0.75) - series.quantile(0.25),
                'Varianza': series.var(),
                'Desv. Est.': series.std(),
                'Coef. Var.': (series.std() / series.mean()) if series.mean() != 0 else 0,
                'Asimetría': series.skew(),
                'Curtosis': series.kurtosis(),
                'Cuenta': series.count(),
                'Suma': series.sum(),
            })
        
        # Generar tabla HTML
        table_html = "<table class='df-table' style='width:100%;'>"
        table_html += "<thead><tr><th>Métrica</th>" + "".join(f"<th>{col}</th>" for col in num_cols) + "</tr></thead>"
        table_html += "<tbody>"
        
        # Obtener todas las métricas
        if stats_list:
            metric_keys = [k for k in stats_list[0].keys() if k != 'Variable']
            for metric in metric_keys:
                table_html += "<tr><td><strong>" + metric + "</strong></td>"
                for row in stats_list:
                    value = row[metric]
                    if isinstance(value, float):
                        value = round(value, 3)
                    table_html += f"<td>{value}</td>"
                table_html += "</tr>"
        
        table_html += "</tbody></table>"
        
        return ui.HTML(table_html)
    
    @output
    @render.ui
    def eda_categorical_stats():
        import pandas as pd

        df = df_current()
        if df is None:
            return ui.div()
        
        cat_cols = get_cat_cols(df)
        
        if not cat_cols:
            return ui.div("No hay variables categóricas seleccionadas.")
        
        stats_list = []
        total_rows = len(df)
        
        for col in cat_cols:
            series = df[col]
            value_counts = series.value_counts(dropna=False)
            
            top_value = value_counts.index[0] if not value_counts.empty else None
            top_freq = value_counts.iloc[0] if not value_counts.empty else 0
            top_pct = (top_freq / total_rows) if total_rows > 0 else 0
            
            stats_list.append({
                'Variable': col,
                'Únicos': series.nunique(dropna=True),
                'Total': total_rows,
                'Moda': str(top_value),
                'Frecuencia moda': top_freq,
                '% Moda': round(top_pct, 3),
            })
        
        df_stats = pd.DataFrame(stats_list)
        
        return ui.HTML(df_stats.to_html(classes='df-table', border=0, index=False))
    
    @output
    @render.ui
    def eda_numeric_distribution():
        df = df_current()
        if df is None:
            return ui.div()
        
        selected = get_num_cols(df)
        
        if not selected:
            return ui.div("Selecciona al menos una variable numérica para ver la distribución.")
        
        cards = []
        for col in selected:
            fig = make_numeric_distribution_figure(df, col)
            cards.append(
                ui.div(
                    ui.div(col, class_="card-title"),
                    render_plotly_html(fig, height=450),
                    class_="sub-card"
                )
            )
        
        return ui.div(*cards, class_="cards-grid")

    @output
    @render.ui
    def eda_categorical_distribution():
        df = df_current()
        if df is None:
            return ui.div()
        
        selected = get_cat_cols(df)

        if not selected:
            return ui.div("Selecciona al menos una variable categórica para ver la distribución.")
        
        cards = []
        for col in selected:
            fig = make_categorical_distribution_figure(df, col)
            cards.append(
                ui.div(
                    ui.div(col, class_="card-title"),
                    render_plotly_html(fig, height=450),
                    class_="sub-card"
                )
            )
        
        return ui.div(*cards, class_="cards-grid")

    @output
    @render.ui
    def eda_shapiro_results():
        df = df_current()
        if df is None:
            return ui.div()
        
        selected = get_num_cols(df)
        
        """
        selected = input.eda_num_cols() or get_num_cols(df)
        selected = [col for col in selected if col in df.columns]
        """

        if not selected:
            return ui.div("Selecciona al menos una variable numérica para ver el test de Shapiro-Wilk.")
        
        return ui.HTML(shapiro_wilk_table_html(df, selected))
    
    @output
    @render.ui
    def eda_correlation_distribution():
        df = df_current()
        if df is None:
            return ui.div()
        
        col_x = input.eda_bivar_x()
        col_y = input.eda_bivar_y()
        col_color = input.eda_bivar_color()
        if not col_color: 
            col_color = None
        
        if not col_x or not col_y or col_x not in df.columns or col_y not in df.columns:
            return ui.div("Selecciona las variables X e Y.")
            
        fig = make_scatter_plot_figure(df, col_x, col_y, col_color)
        return render_plotly_html(fig, height=450)
    
    @output
    @render.ui
    def eda_cov_plot():
        df = df_current()
        if df is None:
            return ui.div()
            
        selected = input.eda_num_cols()
        selected = [col for col in selected if col in df.columns]

        if len(selected) > 10:
            return ui.div(
                ui.tags.h3("Matriz de covarianza", class_="card-title"),
                ui.p(
                    f"Seleccionaste {len(selected)} variables. El límite es 10 para asegurar precisión visual.", 
                    style="color: orange; font-weight: bold; padding: 10px;"
                )
            )
        
        if len(selected) < 2:
            return ui.div("Selecciona al menos dos variables numéricas en la configuración.")
            
        fig = make_cov_heatmap(df, selected)
        
        legend_cov = """
        <div style="margin-top: 16px; color: var(--muted); font-size: 12px; line-height: 1.6;">
          <strong>Leyenda de Covarianza (No Estandarizada):</strong><br>
          <strong>Magnitud:</strong> Depende de las unidades originales de los datos (no está limitada a -1 y 1). Mide la <em>dirección</em> conjunta.<br>
          <strong>Positiva (> 0):</strong> Las variables tienden a moverse en la misma dirección.<br>
          <strong>Negativa (< 0):</strong> Las variables tienden a moverse en direcciones opuestas.<br>
          <strong>Importante:</strong> Un número grande no significa necesariamente una relación "más fuerte" que un número pequeño, solo refleja la escala de los datos.
        </div>
        """
        
        return ui.div(
            ui.tags.h3("Matriz de covarianza", class_="card-title"), 
            render_plotly_html(fig, height=520),
            ui.HTML(legend_cov) # Añadimos la leyenda al final del contenedor
        )
    @output
    @render.ui
    def eda_global_outliers():
        df = df_current()
        if df is None:
            return ui.div()
        column = input.eda_dist_col()
        html_report = outlier_report_html(df[[column]], method="iqr")
        
        return ui.HTML(html_report)