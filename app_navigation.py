from shiny import ui


def sidebar_nav_ui(current_page, current_role="user"):
    def nav_button(button_id, icon, label, page_name):
        is_active = current_page == page_name
        button_class = "nav-btn active" if is_active else "nav-btn"

        return ui.input_action_button(
            button_id,
            ui.HTML(f'<span class="nav-icon">{icon}</span> {label}'),
            class_=button_class,
        )

    def nav_section(title):
        return ui.div(title, class_="nav-section-title")

    items = [
        ui.div(
            nav_section("MODO DE VISTA"),
            ui.input_select(
                "user_role",
                "",
                choices={
                    "user": "👤 Familiar / Usuario",
                    "analyst": "🔬 Analista / Técnico",
                },
                selected=current_role,
            ),
            class_="role-selector-wrap"
        ),

        nav_button("nav_home", "🏠", "Inicio", "home"),
    ]

    if current_role == "user":
        items.extend([
            nav_section("VISTA USUARIO / FAMILIAR"),
            nav_button("nav_patient_search", "🔎", "Consultar paciente", "patient_search"),
            nav_button("nav_resource_availability", "📦", "Estado de recursos", "resource_availability"),
        ])

    elif current_role == "analyst":
        items.extend([
            nav_section("VISTA TÉCNICA / ANALISTA"),
            nav_button("nav_overview", "📊", "Overview", "overview"),
            nav_button("nav_eda", "📈", "EDA", "eda"),
            nav_button("nav_missing", "🧩", "Missing Values", "missing"),
            nav_button("nav_outlier", "🎯", "Outliers", "outlier"),
            nav_button("nav_encode", "🔢", "Encoding", "encode"),
            nav_button("nav_scale", "⚖️", "Scaling", "scale"),
            nav_button("nav_drop", "🗑️", "Feature Selection", "drop"),
            nav_button("nav_model", "🤖", "Modelling", "model"),
            nav_button("nav_export", "💾", "Export", "export"),
            nav_button("nav_docs", "📚", "Docs", "docs"),
        ])

    return ui.div(*items)