"""Home / Care Portal page"""
from shiny import ui


def render_home(df=None):
    """Render ALDIMI user-oriented home page"""

    has_patient_data = df is not None and "patient_code" in df.columns
    has_resource_data = df is not None and "resource_code" in df.columns

    dataset_label = "Sin dataset cargado"
    dataset_description = "Carga un dataset clínico o logístico para visualizar indicadores del sistema."

    patient_count = "—"
    high_risk_count = "—"
    urgent_count = "—"
    patient_localities = "—"

    resource_count = "—"
    shortage_count = "—"
    critical_resources = "—"
    resource_localities = "—"

    if has_patient_data:
        dataset_label = "Dataset clínico cargado"
        dataset_description = "Indicadores asociados a pacientes, riesgo clínico y priorización de seguimiento."

        patient_count = len(df)

        if "Thyroid_Cancer_Risk" in df.columns:
            high_risk_count = df["Thyroid_Cancer_Risk"].astype(str).str.contains(
                "High|Alto", case=False, na=False
            ).sum()

        if "contact_priority" in df.columns:
            urgent_count = df["contact_priority"].astype(str).str.contains(
                "URGENTE|Alta|High", case=False, na=False
            ).sum()

        if "locality" in df.columns:
            patient_localities = df["locality"].dropna().nunique()

    elif has_resource_data:
        dataset_label = "Dataset logístico cargado"
        dataset_description = "Indicadores asociados a recursos, inventario y disponibilidad logística."

        resource_count = len(df)

        if "supply_status" in df.columns:
            shortage_count = df["supply_status"].astype(str).str.contains(
                "Riesgo de escasez|escasez|Crítico|Critico", case=False, na=False
            ).sum()

        if "criticality_level" in df.columns:
            critical_resources = df["criticality_level"].astype(str).str.contains(
                "Alta|High|Crítica|Critica", case=False, na=False
            ).sum()

        if "locality" in df.columns:
            resource_localities = df["locality"].dropna().nunique()

    if has_patient_data:
        kpis = ui.div(
            kpi_card("Pacientes registrados", patient_count, "Casos disponibles para consulta clínica"),
            kpi_card("Casos de alto riesgo", high_risk_count, "Según información registrada", danger=True),
            kpi_card("Prioridad urgente", urgent_count, "Pacientes que requieren seguimiento", danger=True),
            kpi_card("Localidades atendidas", patient_localities, "Cobertura territorial simulada"),
            class_="portal-kpi-grid"
        )

    elif has_resource_data:
        kpis = ui.div(
            kpi_card("Recursos registrados", resource_count, "Recursos disponibles para consulta logística"),
            kpi_card("Recursos en riesgo", shortage_count, "Recursos bajo stock mínimo", danger=True),
            kpi_card("Criticidad alta", critical_resources, "Recursos considerados prioritarios", danger=True),
            kpi_card("Localidades atendidas", resource_localities, "Cobertura territorial simulada"),
            class_="portal-kpi-grid"
        )

    else:
        kpis = ui.div(
            kpi_card("Pacientes", "—", "Carga un dataset clínico"),
            kpi_card("Recursos", "—", "Carga un dataset logístico"),
            kpi_card("Modelos", "2", "Clasificación y regresión"),
            kpi_card("Módulos", "3", "Inicio, pacientes y recursos"),
            class_="portal-kpi-grid"
        )

    return ui.div(
        ui.div(
            ui.div(
                ui.div("SISTEMA DE APOYO A LA DECISIÓN", class_="portal-eyebrow"),
                ui.tags.h1("Portal de Atención ALDIMI", class_="portal-title"),
                ui.p(
                    "Consulta pacientes, prioriza casos clínicos y revisa disponibilidad de recursos "
                    "mediante modelos de Machine Learning.",
                    class_="portal-subtitle"
                ),
                ui.div(dataset_label, class_="dataset-pill"),
                ui.p(dataset_description, class_="portal-description"),
                ui.div(
                    ui.input_action_button(
                        "quick_patient",
                        "Consultar paciente",
                        class_="btn btn-primary portal-btn"
                    ),
                    ui.input_action_button(
                        "quick_resource",
                        "Ver recursos",
                        class_="btn btn-secondary portal-btn"
                    ),
                    class_="portal-actions"
                ),
                class_="portal-hero-content"
            ),
            class_="portal-hero"
        ),

        kpis,

        ui.div(
            module_card(
                "01",
                "Consulta Paciente",
                "Búsqueda por código, nombre o localidad. Muestra datos básicos, riesgo predicho, prioridad de contacto y recomendación.",
                "Random Forest Classifier"
            ),
            module_card(
                "02",
                "Disponibilidad de Recursos",
                "Consulta recursos logísticos, estima inventario y genera alertas de abastecimiento según el stock mínimo requerido.",
                "Regresión Lineal"
            ),
            module_card(
                "03",
                "Módulo Técnico",
                "Incluye EDA, valores nulos, outliers, encoding, scaling, selección de variables y entrenamiento de modelos.",
                "CRISP-DM / ML Pipeline"
            ),
            class_="portal-module-grid"
        ),

        ui.div(
            ui.div(
                ui.div("Flujo de decisión", class_="card-title"),
                ui.div(
                    ui.div("Datos", class_="portal-flow-step"),
                    ui.div("→", class_="portal-flow-arrow"),
                    ui.div("Preprocesamiento", class_="portal-flow-step"),
                    ui.div("→", class_="portal-flow-arrow"),
                    ui.div("Modelo ML", class_="portal-flow-step"),
                    ui.div("→", class_="portal-flow-arrow"),
                    ui.div("Recomendación", class_="portal-flow-step active"),
                    class_="portal-flow"
                ),
                ui.p(
                    "El sistema transforma predicciones en información entendible para apoyar decisiones clínicas y logísticas.",
                    class_="portal-text"
                ),
                class_="card"
            ),

            ui.div(
                ui.div("Nota ética y de uso", class_="card-title"),
                ui.p(
                    "Las predicciones no reemplazan la evaluación médica ni la gestión profesional de abastecimiento. "
                    "Funcionan como apoyo preliminar para priorizar atención y recursos.",
                    class_="portal-text"
                ),
                class_="card"
            ),

            class_="portal-bottom-grid"
        )
    )


def kpi_card(label, value, subtitle, danger=False):
    value_class = "portal-kpi-value danger" if danger else "portal-kpi-value"

    return ui.div(
        ui.div(label, class_="portal-kpi-label"),
        ui.div(str(value), class_=value_class),
        ui.div(subtitle, class_="portal-kpi-sub"),
        class_="portal-kpi-card"
    )


def module_card(number, title, text, tag):
    return ui.div(
        ui.div(number, class_="portal-module-number"),
        ui.div(title, class_="portal-module-title"),
        ui.p(text, class_="portal-text"),
        ui.div(tag, class_="portal-tag"),
        class_="portal-module-card"
    )