"""Missing values page"""
from shiny import ui, render, reactive
from app_helpers import (
    df_preview_html as build_df_preview_html,
    missing_report_html as build_missing_report_html,
    get_num_cols,
    get_cat_cols,
    missing_categories as MISSING_CATEGORIES,
)


def render_missing(df):
    """Render the missing values page"""
    if df is None:
        return ui.div("Sin datos")

    cols_with_null = df.columns[df.isnull().any()].tolist()
    num_cols = get_num_cols(df)
    cat_cols = get_cat_cols(df)

    if not cols_with_null:
        return ui.div(
            ui.div(ui.tags.h2("Valores Faltantes", class_="section-title"),
                   ui.p("Imputación y eliminación de NaN", class_="section-sub")),
            ui.div(ui.HTML('<span style="color:var(--accent);font-size:1.2rem;">✓</span> No hay valores faltantes en el dataset actual.'),
                   class_="card")
        )

    col_options = {"_all_": "— Todas con nulos —"} | {c: f"{c} ({df[c].isnull().sum()} nulos)" for c in cols_with_null}
    strat_num = {"mean": "Media", "median": "Mediana", "mode": "Moda", "constant": "Constante", "drop_rows": "Eliminar filas", "drop_col": "Eliminar columna"}
    strat_cat = {"mode": "Moda", "constant": "Constante (unknown)", "drop_rows": "Eliminar filas", "drop_col": "Eliminar columna"}

    return ui.div(
        ui.div(ui.tags.h2("Valores Faltantes", class_="section-title"),
               ui.p("Imputación y eliminación de NaN", class_="section-sub")),

        ui.div(
            ui.div("CONFIGURAR IMPUTACIÓN", class_="card-title"),
            ui.div(
                ui.div(
                    ui.input_select("miss_col", "Columna:", col_options),
                    class_="ctrl-group"
                ),
                ui.div(
                    ui.input_select("miss_strat_num", "Estrategia (numéricas):", strat_num),
                    class_="ctrl-group"
                ),
                ui.div(
                    ui.input_select("miss_strat_cat", "Estrategia (categóricas):", strat_cat),
                    class_="ctrl-group"
                ),
                ui.div(
                    ui.input_text("miss_constant", "Valor constante (si aplica):", value="0"),
                    class_="ctrl-group"
                ),
                class_="ctrl-row"
            ),
            ui.input_action_button("apply_missing", "Aplicar imputación", class_="btn btn-primary"),
            ui.tags.span(" "),
            ui.input_action_button("reset_missing", "Resetear columna", class_="btn btn-danger"),
            class_="card"
        ),

        ui.div(
            ui.div(
                ui.input_action_button("jump_docs", "!", class_="info-icon"),
                ui.tags.span("ESTADO ACTUAL DE NULOS", style="margin-left:8px;"),
                class_="card-title"
            ),
            ui.output_ui("missing_status"),
            class_="card"
        ),

        ui.div(
            ui.div("PREVIEW", class_="card-title"),
            ui.HTML(build_df_preview_html(df)),
            class_="card"
        )
    )


def register_missing_handlers(input, output, session, df_current, current_page, add_log):
    """Register missing values page handlers"""
    
    @output
    @render.ui
    def missing_status():
        df = df_current()
        if df is None:
            return ui.div()
        report = build_missing_report_html(df)
        if df.isnull().sum().sum() == 0:
            return ui.HTML('<span style="color:var(--accent)">✓ Sin valores faltantes</span>')
        return ui.HTML(report)

    @reactive.Effect
    @reactive.event(input.jump_docs)
    def _jump_docs_from_missing():
        current_page.set("docs")

    @reactive.Effect
    @reactive.event(input.apply_missing)
    def _apply_missing():
        df = df_current().copy()
        col_sel = input.miss_col()
        strat_num = input.miss_strat_num()
        strat_cat = input.miss_strat_cat()
        const_val = input.miss_constant()
        num_cols = get_num_cols(df)
        cat_cols = get_cat_cols(df)

        def impute_col(df, col):
            dtype = "num" if col in num_cols else "cat"
            strat = strat_num if dtype == "num" else strat_cat
            n_before = df[col].isnull().sum()
            if n_before == 0:
                return df
            if strat == "mean":
                df[col].fillna(df[col].mean(), inplace=True)
            elif strat == "median":
                df[col].fillna(df[col].median(), inplace=True)
            elif strat == "mode":
                df[col].fillna(df[col].mode()[0], inplace=True)
            elif strat == "constant":
                fill_val = float(const_val) if dtype == "num" else (const_val or "unknown")
                df[col].fillna(fill_val, inplace=True)
            elif strat == "drop_rows":
                df.dropna(subset=[col], inplace=True)
            elif strat == "drop_col":
                df.drop(columns=[col], inplace=True)
            return df

        if col_sel == "_all_":
            for col in df.columns[df.isnull().any()].tolist():
                df = impute_col(df, col)
            add_log(f"Imputación aplicada a todas las columnas con nulos")
        else:
            df = impute_col(df, col_sel)
            add_log(f"Imputación aplicada a '{col_sel}'")

        df_current.set(df)
