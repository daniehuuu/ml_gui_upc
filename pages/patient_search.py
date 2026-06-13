"""Patient Search page"""
from shiny import ui, render, reactive
from html import escape


def render_patient_search(df):
    """Render patient search page"""
    if df is None:
        return ui.div("Sin datos")

    required_cols = ["patient_code", "patient_name"]
    missing_cols = [c for c in required_cols if c not in df.columns]

    if missing_cols:
        return ui.div(
            ui.div(
                ui.tags.h2("Consulta Paciente", class_="section-title"),
                ui.p(
                    "Búsqueda de pacientes por código, nombre, localidad o prioridad de contacto",
                    class_="section-sub"
                )
            ),
            ui.div(
                f"El dataset no contiene las columnas necesarias: {missing_cols}",
                class_="card"
            )
        )

    return ui.div(
        ui.div(
            ui.tags.h2("Consulta Paciente", class_="section-title"),
            ui.p(
                "Búsqueda de pacientes por código, nombre, localidad o prioridad de contacto",
                class_="section-sub"
            )
        ),

        ui.div(
            ui.div("BUSCAR PACIENTE", class_="card-title"),

            ui.div(
                ui.div(
                    ui.input_text(
                        "patient_query",
                        "Código o nombre del paciente:",
                        placeholder="Ejemplo: PAC-00001, Santiago, Lima, Puno..."
                    ),
                    class_="ctrl-group"
                ),
                ui.div(
                    ui.input_select(
                        "patient_priority_filter",
                        "Prioridad:",
                        {
                            "all": "Todas",
                            "URGENTE": "URGENTE",
                            "MODERADA": "MODERADA",
                            "RUTINA": "RUTINA",
                        },
                        selected="all"
                    ),
                    class_="ctrl-group"
                ),
                ui.div(
                    ui.input_select(
                        "patient_risk_filter",
                        "Riesgo clínico:",
                        {
                            "all": "Todos",
                            "High": "High",
                            "Medium": "Medium",
                            "Low": "Low",
                        },
                        selected="all"
                    ),
                    class_="ctrl-group"
                ),
                class_="ctrl-row"
            ),

            ui.input_action_button(
                "search_patient",
                "Buscar",
                class_="btn btn-primary",
                style="width:100%;"
            ),

            class_="card"
        ),

        ui.div(
            ui.div("RESULTADOS DE BÚSQUEDA", class_="card-title"),
            ui.output_ui("patient_search_results"),
            class_="card"
        ),

        ui.div(
            ui.div("DETALLE DEL PACIENTE", class_="card-title"),
            ui.output_ui("patient_detail"),
            class_="card"
        )
    )


def register_patient_search_handlers(input, output, df_current):
    """Register patient search handlers"""

    selected_patient_code = reactive.Value(None)

    def risk_badge(risk):
        risk_str = str(risk).strip()

        if risk_str == "High":
            color = "var(--accent2)"
            label = "Alto"
        elif risk_str == "Medium":
            color = "var(--warn)"
            label = "Medio"
        elif risk_str == "Low":
            color = "var(--accent)"
            label = "Bajo"
        else:
            color = "var(--muted)"
            label = risk_str if risk_str else "Sin dato"

        return f"<span class='pill' style='background:{color};color:#fff'>{escape(label)}</span>"

    def priority_badge(priority):
        priority_str = str(priority).strip()

        if priority_str == "URGENTE":
            color = "var(--accent2)"
        elif priority_str == "MODERADA":
            color = "var(--warn)"
        elif priority_str == "RUTINA":
            color = "var(--accent)"
        else:
            color = "var(--muted)"
            priority_str = priority_str if priority_str else "Sin dato"

        return f"<span class='pill' style='background:{color};color:#fff'>{escape(priority_str)}</span>"

    def diagnosis_badge(diagnosis):
        diagnosis_str = str(diagnosis).strip()

        if diagnosis_str == "Malignant":
            color = "var(--accent2)"
            label = "Malignant"
        elif diagnosis_str == "Benign":
            color = "var(--accent)"
            label = "Benign"
        else:
            color = "var(--muted)"
            label = diagnosis_str if diagnosis_str else "Sin dato"

        return f"<span class='pill' style='background:{color};color:#fff'>{escape(label)}</span>"

    def recommendation_text(risk, diagnosis, priority):
        risk = str(risk).strip()
        diagnosis = str(diagnosis).strip()
        priority = str(priority).strip()

        if diagnosis == "Malignant" or risk == "High" or priority == "URGENTE":
            return (
                "Priorizar seguimiento clínico. Se recomienda derivación o evaluación médica "
                "especializada y monitoreo cercano del caso."
            )

        if risk == "Medium" or priority == "MODERADA":
            return (
                "Mantener vigilancia periódica. Se recomienda control endocrino, revisión de "
                "biomarcadores y seguimiento del tamaño del nódulo."
            )

        return (
            "Mantener seguimiento preventivo estándar. Se recomienda control anual y "
            "monitoreo si aparecen nuevos factores de riesgo."
        )

    def safe_get(row, col, default="Sin dato"):
        value = row.get(col, default)
        if value is None:
            return default
        value_str = str(value)
        if value_str.strip() == "" or value_str.strip().lower() == "nan":
            return default
        return value_str

    def info_row(label, value, html_value=False):
        if html_value:
            rendered_value = value
        else:
            rendered_value = escape(str(value))

        return f"""
        <div class="info-row">
            <span class="info-label">{escape(str(label))}</span>
            <span class="info-value">{rendered_value}</span>
        </div>
        """

    @reactive.Effect
    @reactive.event(input.search_patient)
    def _clear_selected_patient():
        selected_patient_code.set(None)

    @reactive.Effect
    @reactive.event(input.selected_patient_code)
    def _select_patient_from_table():
        selected_patient_code.set(input.selected_patient_code())

    @output
    @render.ui
    def patient_search_results():
        df = df_current()

        if df is None:
            return ui.div()

        required = ["patient_code", "patient_name"]
        if any(c not in df.columns for c in required):
            return ui.div("No se encontraron columnas de paciente en el dataset.")

        query = input.patient_query() or ""
        query = query.strip().lower()

        priority_filter = input.patient_priority_filter()
        risk_filter = input.patient_risk_filter()

        filtered = df.copy()

        if query:
            search_cols = [
                c for c in [
                    "patient_code",
                    "patient_name",
                    "locality",
                    "assigned_program",
                    "contact_priority",
                    "Thyroid_Cancer_Risk",
                    "Diagnosis"
                ]
                if c in filtered.columns
            ]

            mask = False
            for col in search_cols:
                mask = mask | filtered[col].astype(str).str.lower().str.contains(query, na=False)

            filtered = filtered[mask]

        if priority_filter != "all" and "contact_priority" in filtered.columns:
            filtered = filtered[filtered["contact_priority"] == priority_filter]

        if risk_filter != "all" and "Thyroid_Cancer_Risk" in filtered.columns:
            filtered = filtered[filtered["Thyroid_Cancer_Risk"] == risk_filter]

        if filtered.empty:
            return ui.div(
                "No se encontraron pacientes con esos criterios.",
                style="color: var(--muted);"
            )

        filtered = filtered.head(15)

        rows = ""

        for _, row in filtered.iterrows():
            code = safe_get(row, "patient_code")
            name = safe_get(row, "patient_name")
            age = safe_get(row, "Age")
            locality = safe_get(row, "locality")
            priority = safe_get(row, "contact_priority")
            risk = safe_get(row, "Thyroid_Cancer_Risk")

            rows += f"""
            <tr>
                <td>
                    <button 
                        type="button" 
                        class="btn btn-secondary"
                        onclick="Shiny.setInputValue('selected_patient_code', '{escape(code)}', {{priority: 'event'}})"
                    >
                        Ver
                    </button>
                </td>
                <td>{escape(code)}</td>
                <td>{escape(name)}</td>
                <td>{escape(age)}</td>
                <td>{escape(locality)}</td>
                <td>{priority_badge(priority)}</td>
                <td>{risk_badge(risk)}</td>
            </tr>
            """

        return ui.HTML(f"""
        <div class="df-table-wrap">
            <table class="df-table">
                <thead>
                    <tr>
                        <th>Acción</th>
                        <th>Código</th>
                        <th>Paciente</th>
                        <th>Edad</th>
                        <th>Localidad</th>
                        <th>Prioridad</th>
                        <th>Riesgo</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        <div style="color:var(--muted);font-size:11px;margin-top:8px;">
            Mostrando máximo 15 resultados. Presiona “Ver” para revisar el detalle.
        </div>
        """)

    @output
    @render.ui
    def patient_detail():
        df = df_current()

        if df is None:
            return ui.div()

        code = selected_patient_code()

        if not code:
            return ui.div(
                "Selecciona un paciente desde los resultados de búsqueda.",
                style="color: var(--muted);"
            )

        patient_df = df[df["patient_code"].astype(str) == str(code)]

        if patient_df.empty:
            return ui.div("No se encontró el paciente seleccionado.")

        row = patient_df.iloc[0]

        patient_code = safe_get(row, "patient_code")
        patient_name = safe_get(row, "patient_name")
        age = safe_get(row, "Age")
        gender = safe_get(row, "Gender")
        locality = safe_get(row, "locality")
        admission_date = safe_get(row, "admission_date")
        country = safe_get(row, "Country")
        ethnicity = safe_get(row, "Ethnicity")
        assigned_program = safe_get(row, "assigned_program")
        contact_priority = safe_get(row, "contact_priority")
        risk = safe_get(row, "Thyroid_Cancer_Risk")
        diagnosis = safe_get(row, "Diagnosis")

        recommendation = recommendation_text(risk, diagnosis, contact_priority)
        urgent_class = "urgent" if str(contact_priority).strip() == "URGENTE" else ""

        clinical_rows = ""
        for col in [
            "Family_History",
            "Radiation_Exposure",
            "Iodine_Deficiency",
            "Smoking",
            "Obesity",
            "Diabetes",
            "TSH_Level",
            "T3_Level",
            "T4_Level",
            "Nodule_Size",
        ]:
            if col in df.columns:
                clinical_rows += f"""
                <tr>
                    <td>{escape(col)}</td>
                    <td>{escape(safe_get(row, col))}</td>
                </tr>
                """

        basic_info_html = (
            info_row("Código", patient_code)
            + info_row("Paciente", patient_name)
            + info_row("Edad", age)
            + info_row("Género", gender)
            + info_row("Localidad", locality)
            + info_row("Fecha de ingreso", admission_date)
            + info_row("País", country)
            + info_row("Grupo étnico", ethnicity)
        )

        clinical_priority_html = (
            info_row("Riesgo estimado", risk_badge(risk), html_value=True)
            + info_row("Diagnóstico", diagnosis_badge(diagnosis), html_value=True)
            + info_row("Prioridad de contacto", priority_badge(contact_priority), html_value=True)
            + info_row("Programa asignado", assigned_program)
        )

        return ui.HTML(f"""
        <div class="detail-grid">
            <div class="sub-card-clean">
                <div class="section-block-title">Datos básicos</div>
                <div class="info-list">
                    {basic_info_html}
                </div>
            </div>

            <div class="sub-card-clean">
                <div class="section-block-title">Priorización clínica</div>
                <div class="info-list">
                    {clinical_priority_html}
                </div>
            </div>

            <div class="sub-card-clean">
                <div class="section-block-title">Recomendación</div>
                <div class="recommendation-box {urgent_class}">
                    {escape(recommendation)}
                </div>
            </div>
        </div>

        <br>

        <div class="section-block-title">Variables clínicas del paciente</div>
        <div class="df-table-wrap">
            <table class="df-table">
                <thead>
                    <tr>
                        <th>Variable</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    {clinical_rows}
                </tbody>
            </table>
        </div>
        """)