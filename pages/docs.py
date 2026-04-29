"""Documentation page"""
from shiny import ui


def render_docs(df):
    """Render the documentation page"""
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
