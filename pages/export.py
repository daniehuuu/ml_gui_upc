"""Export page"""
from shiny import ui, render


def render_export(df, df_original, ops_log):
    """Render the export page"""
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


def register_export_handlers(input, output, df_current):
    """Register export page handlers"""
    
    @output
    @render.download(filename="dataset_preprocesado.csv")
    def download_csv():
        df = df_current()
        if df is None:
            yield ""
            return
        yield df.to_csv(index=False)
