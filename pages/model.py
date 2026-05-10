"""Classification modelling page"""
from shiny import ui, render, reactive
from app_helpers import get_num_cols, get_cat_cols


def render_model(df):
    """Render the classification modelling page"""
    if df is None:
        return ui.div("Sin datos")

    num_cols = get_num_cols(df)
    cat_cols = get_cat_cols(df)

    return ui.div(
        ui.div(
            ui.tags.h2("Classification Modelling", class_="section-title"),
            ui.p("Entrenamiento y evaluación de un modelo de clasificación supervisada", class_="section-sub")
        ),

        ui.div(
            ui.div("CONFIGURACIÓN DEL MODELO DE CLASIFICACIÓN", class_="card-title"),

            ui.input_select(
                "target_col",
                "Seleccione la variable objetivo:",
                choices=list(df.columns)
            ),

            ui.input_checkbox_group(
                "feature_cols",
                "Seleccione las variables predictoras:",
                choices=[],
                selected=[]
            ),

            ui.tags.br(),

            ui.input_action_button(
                "train_model",
                "Entrenar modelo de clasificación",
                class_="btn btn-primary"
            ),

            class_="card"
        ),

        ui.div(
            ui.div("VARIABLES DISPONIBLES", class_="card-title"),
            ui.HTML("".join(
                f'<span class="pill {"pill-num" if c in num_cols else "pill-cat"}">{c}</span>'
                for c in df.columns
            )),
            class_="card"
        ),

        ui.div(
            ui.div("RESULTADOS DEL MODELO", class_="card-title"),
            ui.output_ui("model_results"),
            class_="card"
        )
    )


def register_model_handlers(input, output, df_current, add_log):
    """Register classification modelling handlers"""

    model_state = reactive.Value(None)

    @reactive.Effect
    def _update_feature_choices():
        df = df_current()
        if df is None:
            return

        target = input.target_col()
        if not target:
            return

        features = [c for c in df.columns if c != target]

        ui.update_checkbox_group(
            "feature_cols",
            choices=features,
            selected=features
        )

    @reactive.Effect
    @reactive.event(input.train_model)
    def _train_model():
        df = df_current()

        if df is None:
            ui.notification_show("No hay dataset cargado.", type="error")
            return

        target = input.target_col()
        features = list(input.feature_cols())

        if not target:
            ui.notification_show("Seleccione una variable objetivo.", type="error")
            return

        if target in features:
            features.remove(target)

        if not features:
            ui.notification_show("Debe seleccionar al menos una variable predictora.", type="error")
            return

        model_state.set({
            "target": target,
            "features": features,
            "n_features": len(features),
            "n_rows": df.shape[0]
        })

        add_log(f"Clasificación configurada | Target: {target} | Features: {len(features)}")
        ui.notification_show("Configuración del modelo de clasificación registrada correctamente.", type="success")

    @output
    @render.ui
    def model_results():
        state = model_state()

        if state is None:
            return ui.p(
                "Aún no se ha entrenado ningún modelo. Seleccione la variable objetivo, las variables predictoras y presione 'Entrenar modelo de clasificación'.",
                style="color: var(--muted);"
            )

        return ui.div(
            ui.p("Tipo de modelo: Clasificación supervisada"),
            ui.p(f"Variable objetivo: {state['target']}"),
            ui.p(f"Variables predictoras seleccionadas: {state['n_features']}"),
            ui.p(f"Registros utilizados: {state['n_rows']}"),
        )