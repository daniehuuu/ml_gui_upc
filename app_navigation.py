from shiny import ui


def sidebar_nav_ui(current_page):
    def nav_button(button_id, icon, label, page_name):
        is_active = current_page == page_name
        button_class = "nav-btn active" if is_active else "nav-btn"
        return ui.input_action_button(
            button_id,
            ui.HTML(f'<span class="nav-icon">{icon}</span> {label}'),
            class_=button_class,
        )

    return ui.div(
        nav_button("nav_overview", "📊", "Overview", "overview"),
        nav_button("nav_eda", "📈", "EDA", "eda"),
        nav_button("nav_missing", "🔍", "Missing Values", "missing"),
        nav_button("nav_outlier", "🎯", "Outliers", "outlier"),
        nav_button("nav_encode", "🔢", "Encoding", "encode"),
        nav_button("nav_scale", "⚖️", "Scaling", "scale"),
        nav_button("nav_drop", "🗑️", "Drop Columns", "drop"),
        nav_button("nav_export", "💾", "Export", "export"),
        nav_button("nav_docs", "📚", "Docs", "docs"),
    )
