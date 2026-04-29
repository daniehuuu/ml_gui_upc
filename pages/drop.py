"""Drop columns page"""
from shiny import ui, render, reactive
from app_helpers import (
    get_num_cols,
    get_cat_cols,
)


def render_drop(df):
    """Render the drop columns page"""
    if df is None:
        return ui.div("Sin datos")

    col_checkboxes = ui.div(
        *[ui.div(
            ui.input_checkbox(f"drop_{col.replace(' ','_')}", col, value=False),
            class_="check-item"
          ) for col in df.columns],
        class_="check-list"
    )

    return ui.div(
        ui.div(ui.tags.h2("Drop Columns", class_="section-title"),
               ui.p("Eliminar columnas innecesarias del dataset", class_="section-sub")),

        ui.div(
            ui.div("SELECCIONAR COLUMNAS A ELIMINAR", class_="card-title"),
            col_checkboxes,
            ui.tags.br(),
            ui.input_action_button("apply_drop", "Eliminar columnas seleccionadas", class_="btn btn-danger"),
            ui.tags.span(" "),
            ui.input_action_button("reset_df", "Reset completo al original", class_="btn btn-secondary"),
            class_="card"
        ),

        ui.div(
            ui.div("COLUMNAS ACTUALES", class_="card-title"),
            ui.HTML("".join(
                f'<span class="pill {"pill-num" if c in get_num_cols(df) else "pill-cat"}">{c}</span>'
                for c in df.columns
            )),
            class_="card"
        )
    )


def register_drop_handlers(input, output, df_current, df_original, dtype_manual_state, ops_log, add_log):
    """Register drop columns page handlers"""
    
    @reactive.Effect
    @reactive.event(input.apply_drop)
    def _apply_drop():
        df = df_current().copy()
        to_drop = []
        for col in df.columns:
            key = f"drop_{col.replace(' ','_')}"
            try:
                if input[key]():
                    to_drop.append(col)
            except:
                pass
        if to_drop:
            df.drop(columns=to_drop, inplace=True)
            add_log(f"Columnas eliminadas: {to_drop}")
            df_current.set(df)

    @reactive.Effect
    @reactive.event(input.reset_df)
    def _reset_df():
        df_current.set(df_original().copy())
        dtype_manual_state.set({})
        ops_log.set(["Dataset reseteado al original"])
