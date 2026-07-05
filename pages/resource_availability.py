"""Resource Availability page"""
from shiny import ui, render, reactive
from html import escape


def render_resource_availability(df):
    """Render resource availability page"""
    if df is None:
        return ui.div("Sin datos")

    required_cols = ["resource_code", "resource_name"]
    missing_cols = [c for c in required_cols if c not in df.columns]

    if missing_cols:
        return ui.div(
            ui.div(
                ui.tags.h2("Disponibilidad de Recursos", class_="section-title"),
                ui.p(
                    "Consulta de recursos, inventario estimado y alertas de abastecimiento",
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
            ui.tags.h2("Disponibilidad de Recursos", class_="section-title"),
            ui.p(
                "Consulta de recursos logísticos y predicción de inventario mediante el modelo entrenado",
                class_="section-sub"
            )
        ),

        ui.div(
            ui.div("BUSCAR RECURSO", class_="card-title"),

            ui.div(
                ui.div(
                    ui.input_text(
                        "resource_query",
                        "Código, nombre, categoría, almacén o localidad:",
                        placeholder="Ejemplo: RES-00001, Paracetamol, Lima, Medicamento..."
                    ),
                    class_="ctrl-group"
                ),
                ui.div(
                    ui.input_select(
                        "resource_status_filter",
                        "Estado:",
                        {
                            "all": "Todos",
                            "Riesgo de escasez": "Riesgo de escasez",
                            "En observación": "En observación",
                            "Estable": "Estable",
                            "Bien abastecido": "Bien abastecido",
                        },
                        selected="all"
                    ),
                    class_="ctrl-group"
                ),
                ui.div(
                    ui.input_select(
                        "resource_category_filter",
                        "Categoría:",
                        build_category_choices(df),
                        selected="all"
                    ),
                    class_="ctrl-group"
                ),
                class_="ctrl-row"
            ),

            ui.input_action_button(
                "search_resource",
                "Buscar",
                class_="btn btn-primary",
                style="width:100%;"
            ),

            class_="card"
        ),

        ui.div(
            ui.div("RESULTADOS DE BÚSQUEDA", class_="card-title"),
            ui.output_ui("resource_search_results"),
            class_="card"
        ),

        ui.div(
            ui.div("DETALLE DEL RECURSO", class_="card-title"),
            ui.output_ui("resource_detail"),
            class_="card"
        )
    )


def build_category_choices(df):
    if df is None or "resource_category" not in df.columns:
        return {"all": "Todas"}

    categories = sorted(df["resource_category"].dropna().astype(str).unique().tolist())
    return {"all": "Todas", **{cat: cat for cat in categories}}


def register_resource_availability_handlers(
    input,
    output,
    df_original,
    df_processed,
    regression_model_state
):
    """Register resource availability handlers"""

    selected_resource_code = reactive.Value(None)

    def safe_get(row, col, default="Sin dato"):
        value = row.get(col, default)
        if value is None:
            return default
        value_str = str(value)
        if value_str.strip() == "" or value_str.strip().lower() == "nan":
            return default
        return value_str

    def info_row(label, value, html_value=False):
        rendered_value = value if html_value else escape(str(value))

        return f"""
        <div class="info-row">
            <span class="info-label">{escape(str(label))}</span>
            <span class="info-value">{rendered_value}</span>
        </div>
        """

    def status_badge(status):
        status_str = str(status).strip()

        if status_str in ["Riesgo de escasez", "Crítico", "Bajo"]:
            color = "var(--accent2)"
        elif status_str in ["En observación", "Moderado"]:
            color = "var(--warn)"
        elif status_str in ["Estable", "Bien abastecido", "Normal"]:
            color = "var(--accent)"
        else:
            color = "var(--muted)"
            status_str = status_str if status_str else "Sin dato"

        return f"<span class='pill' style='background:{color};color:#fff'>{escape(status_str)}</span>"

    def criticality_badge(level):
        level_str = str(level).strip()

        if level_str in ["Alta", "High", "Crítica"]:
            color = "var(--accent2)"
        elif level_str in ["Media", "Medium"]:
            color = "var(--warn)"
        elif level_str in ["Baja", "Low"]:
            color = "var(--accent)"
        else:
            color = "var(--muted)"
            level_str = level_str if level_str else "Sin dato"

        return f"<span class='pill' style='background:{color};color:#fff'>{escape(level_str)}</span>"

    def calculate_supply_status(predicted_inventory, minimum_required_stock):
        try:
            predicted_inventory = float(predicted_inventory)
            minimum_required_stock = float(minimum_required_stock)
        except Exception:
            return "Sin dato", "No se pudo calcular una recomendación logística."

        if predicted_inventory < minimum_required_stock:
            return (
                "Riesgo de escasez",
                "Priorizar reposición del recurso. El inventario estimado está por debajo del stock mínimo requerido."
            )

        if predicted_inventory < minimum_required_stock * 1.5:
            return (
                "En observación",
                "Monitorear el recurso y evaluar una reposición preventiva."
            )

        return (
            "Estable",
            "Mantener monitoreo regular. El inventario estimado cubre el stock mínimo requerido."
        )

    @reactive.Effect
    @reactive.event(input.search_resource)
    def _clear_selected_resource():
        selected_resource_code.set(None)

    @reactive.Effect
    @reactive.event(input.selected_resource_code)
    def _select_resource_from_table():
        selected_resource_code.set(input.selected_resource_code())

    @output
    @render.ui
    def resource_search_results():
        df = df_original()

        if df is None:
            return ui.div()

        required = ["resource_code", "resource_name"]
        if any(c not in df.columns for c in required):
            return ui.div("No se encontraron columnas de recursos en el dataset.")

        query = input.resource_query() or ""
        query = query.strip().lower()

        status_filter = input.resource_status_filter()
        category_filter = input.resource_category_filter()

        filtered = df.copy()

        if query:
            search_cols = [
                c for c in [
                    "resource_code",
                    "resource_name",
                    "resource_category",
                    "warehouse_name",
                    "locality",
                    "assigned_program",
                    "criticality_level",
                    "supply_status",
                ]
                if c in filtered.columns
            ]

            mask = False
            for col in search_cols:
                mask = mask | filtered[col].astype(str).str.lower().str.contains(query, na=False)

            filtered = filtered[mask]

        if status_filter != "all" and "supply_status" in filtered.columns:
            filtered = filtered[filtered["supply_status"].astype(str) == status_filter]

        if category_filter != "all" and "resource_category" in filtered.columns:
            filtered = filtered[filtered["resource_category"].astype(str) == category_filter]

        if filtered.empty:
            return ui.div(
                "No se encontraron recursos con esos criterios.",
                style="color: var(--muted);"
            )

        filtered = filtered.head(15)

        rows = ""

        for _, row in filtered.iterrows():
            code = safe_get(row, "resource_code")
            name = safe_get(row, "resource_name")
            category = safe_get(row, "resource_category")
            warehouse = safe_get(row, "warehouse_name")
            locality = safe_get(row, "locality")
            min_stock = safe_get(row, "minimum_required_stock")
            status = safe_get(row, "supply_status")

            rows += f"""
            <tr>
                <td>
                    <button 
                        type="button" 
                        class="btn btn-secondary"
                        onclick="Shiny.setInputValue('selected_resource_code', '{escape(code)}', {{priority: 'event'}})"
                    >
                        Ver
                    </button>
                </td>
                <td>{escape(code)}</td>
                <td>{escape(name)}</td>
                <td>{escape(category)}</td>
                <td>{escape(warehouse)}</td>
                <td>{escape(locality)}</td>
                <td class="num-cell">{escape(str(min_stock))}</td>
                <td>{status_badge(status)}</td>
            </tr>
            """

        return ui.HTML(f"""
        <div class="df-table-wrap">
            <table class="df-table">
                <thead>
                    <tr>
                        <th>Acción</th>
                        <th>Código</th>
                        <th>Recurso</th>
                        <th>Categoría</th>
                        <th>Almacén</th>
                        <th>Localidad</th>
                        <th>Stock mínimo</th>
                        <th>Estado</th>
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
    def resource_detail():
        df = df_original()

        if df is None:
            return ui.div()

        code = selected_resource_code()

        if not code:
            return ui.div(
                "Selecciona un recurso desde los resultados de búsqueda.",
                style="color: var(--muted);"
            )

        resource_df = df[df["resource_code"].astype(str) == str(code)]

        if resource_df.empty:
            return ui.div("No se encontró el recurso seleccionado.")

        row = resource_df.iloc[0]

        resource_code = safe_get(row, "resource_code")
        resource_name = safe_get(row, "resource_name")
        resource_category = safe_get(row, "resource_category")
        warehouse_name = safe_get(row, "warehouse_name")
        locality = safe_get(row, "locality")
        assigned_program = safe_get(row, "assigned_program")
        unit_type = safe_get(row, "unit_type")
        minimum_required_stock = safe_get(row, "minimum_required_stock")
        last_restock_date = safe_get(row, "last_restock_date")
        criticality_level = safe_get(row, "criticality_level")
        registered_status = safe_get(row, "supply_status")
        registered_recommendation = safe_get(row, "logistic_recommendation")
        registered_inventory = safe_get(row, "warehouse_inventory_level")

        # ── Predicción con modelo de regresión entrenado ─────────────────────
        model_info = regression_model_state()
        processed_df = df_processed()

        prediction_available = False
        prediction_error = None
        predicted_inventory = None

        if model_info is not None and processed_df is not None:
            try:
                model = model_info.get("best_model")
                features = model_info.get("features", [])

                if "resource_code" not in processed_df.columns:
                    prediction_error = "El dataset procesado no conserva resource_code."
                else:
                    processed_resource = processed_df[
                        processed_df["resource_code"].astype(str) == str(resource_code)
                    ]

                    if processed_resource.empty:
                        prediction_error = "No se encontró este recurso en el dataset procesado."
                    else:
                        missing_features = [
                            feature for feature in features
                            if feature not in processed_resource.columns
                        ]

                        if missing_features:
                            prediction_error = f"Faltan features procesadas: {missing_features}"
                        else:
                            sample_X = processed_resource[features].iloc[[0]].copy()
                            cat_cols = sample_X.select_dtypes(include=["object", "category"]).columns.tolist()

                            if cat_cols:
                                prediction_error = f"Hay variables sin encoding: {cat_cols}"
                            elif sample_X.isnull().any().any():
                                prediction_error = "La fila procesada contiene valores nulos."
                            else:
                                predicted_inventory = float(model.predict(sample_X)[0])
                                prediction_available = True

            except Exception as exc:
                prediction_error = str(exc)
        else:
            prediction_error = "Aún no hay modelo de regresión entrenado."

        inventory_to_show = predicted_inventory if prediction_available else registered_inventory
        status_to_show, recommendation_to_show = calculate_supply_status(
            inventory_to_show,
            minimum_required_stock
        )

        if not prediction_available:
            status_to_show = registered_status
            recommendation_to_show = registered_recommendation

        if prediction_available:
            model_status_html = (
                "<span class='pill' style='background:var(--accent);color:#fff'>"
                "Predicción generada"
                "</span>"
            )
        else:
            model_status_html = (
                "<span class='pill' style='background:var(--warn);color:#000'>"
                "Usando dato registrado"
                "</span>"
            )

        prediction_notice = ""
        if not prediction_available and prediction_error:
            prediction_notice = f"""
            <div class="recommendation-box">
                <b>Nota del modelo:</b> {escape(str(prediction_error))}
            </div>
            <br>
            """

        if prediction_available:
            predicted_inventory_text = f"{predicted_inventory:.2f} {escape(str(unit_type))}"
        else:
            predicted_inventory_text = f"{escape(str(registered_inventory))} {escape(str(unit_type))}"

        resource_info_html = (
            info_row("Código", resource_code)
            + info_row("Recurso", resource_name)
            + info_row("Categoría", resource_category)
            + info_row("Almacén", warehouse_name)
            + info_row("Localidad", locality)
            + info_row("Programa asignado", assigned_program)
        )

        stock_info_html = (
            info_row("Estado del modelo", model_status_html, html_value=True)
            + info_row("Inventario estimado", predicted_inventory_text)
            + info_row("Inventario registrado", f"{registered_inventory} {unit_type}")
            + info_row("Stock mínimo requerido", f"{minimum_required_stock} {unit_type}")
            + info_row("Estado de abastecimiento", status_badge(status_to_show), html_value=True)
            + info_row("Criticidad", criticality_badge(criticality_level), html_value=True)
            + info_row("Última reposición", last_restock_date)
        )

        urgent_class = "urgent" if str(status_to_show).strip() == "Riesgo de escasez" else ""

        logistic_rows = ""
        for col in [
            "lead_time_days",
            "historical_demand",
            "shipping_costs",
            "supplier_reliability_score",
            "delay_probability",
            "disruption_likelihood_score",
            "delivery_time_deviation",
            "customs_clearance_time",
            "weather_condition_severity",
            "traffic_congestion_level",
            "port_congestion_level",
        ]:
            if col in df.columns:
                logistic_rows += f"""
                <tr>
                    <td>{escape(col)}</td>
                    <td>{escape(safe_get(row, col))}</td>
                </tr>
                """

        return ui.HTML(f"""
        {prediction_notice}

        <div class="detail-grid">
            <div class="sub-card-clean">
                <div class="section-block-title">Datos del recurso</div>
                <div class="info-list">
                    {resource_info_html}
                </div>
            </div>

            <div class="sub-card-clean">
                <div class="section-block-title">Abastecimiento</div>
                <div class="info-list">
                    {stock_info_html}
                </div>
            </div>

            <div class="sub-card-clean">
                <div class="section-block-title">Recomendación logística</div>
                <div class="recommendation-box {urgent_class}">
                    {escape(str(recommendation_to_show))}
                </div>
            </div>
        </div>

        <br>

        <div class="section-block-title">Variables logísticas del recurso</div>
        <div class="df-table-wrap">
            <table class="df-table">
                <thead>
                    <tr>
                        <th>Variable</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    {logistic_rows}
                </tbody>
            </table>
        </div>
        """)