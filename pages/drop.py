"""Drop columns page"""
from shiny import ui, render, reactive
from app_helpers import (
    get_num_cols,
    get_cat_cols,
)


def render_drop(df):
    """Render the feature selection page"""
    if df is None:
        return ui.div("Sin datos")

    # PRE-SELECCIÓN INTELIGENTE: 
    # Seleccionamos por defecto todas las columnas que NO empiezan con "_"
    suggested_keep = [c for c in df.columns if not c.startswith('_')]
    hidden_cols = [c for c in df.columns if c.startswith('_')]

    return ui.div(
        ui.div(ui.tags.h2("Feature Selection", class_="section-title"),
               ui.p("Seleccionar las variables finales que ingresarán al modelo", class_="section-sub")),

        ui.div(
            ui.div("VARIABLES A CONSERVAR (Lista Blanca)", class_="card-title"),
            
            ui.p("Las variables temporales (con guion bajo) han sido desmarcadas por defecto para tu comodidad.", 
                 style="color: var(--muted); font-size: 0.9em; margin-bottom: 15px;"),
            
            # Usamos checkbox_group pero con el parámetro 'selected' activado
            ui.input_checkbox_group(
                "cols_to_keep", 
                "Seleccione las columnas que desea MANTENER:", 
                choices=list(df.columns),
                selected=suggested_keep
            ),
            
            ui.tags.br(),
            ui.div(
                ui.input_action_button("apply_keep", "Aplicar Selección (Descartar el resto)", class_="btn btn-primary"),
                ui.tags.span(" "),
                
                # Botón de limpieza rápida con un clic
                ui.input_action_button("clean_hidden", "Limpiar temporales automáticamente", class_="btn btn-warning") if hidden_cols else ui.div(),
                ui.tags.span(" "),
                
                ui.input_action_button("reset_df", "Reset completo al original", class_="btn btn-secondary"),
                class_="btn-group"
            ),
            class_="card"
        ),

        ui.div(
            ui.div("COLUMNAS ACTUALES EN MEMORIA", class_="card-title"),
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
    @reactive.event(input.apply_keep)
    def _apply_keep():
        df = df_current().copy()
        to_keep = list(input.cols_to_keep()) 
        
        if not to_keep:
            ui.notification_show("Error: Debes conservar al menos una variable para el modelo.", type="error")
            return
            
        dropped_count = len(df.columns) - len(to_keep)
        
        # Magia de Pandas: Nos quedamos solo con las seleccionadas
        df = df[to_keep]
        
        add_log(f"Feature Selection: Se conservaron {len(to_keep)} columnas. Se descartaron {dropped_count}.")
        df_current.set(df)
        ui.notification_show(f"Dataset actualizado: Se conservaron {len(to_keep)} variables finales.", type="success")

    # --- Handler para limpieza inteligente con un clic ---
    @reactive.Effect
    @reactive.event(input.clean_hidden)
    def _clean_hidden():
        df = df_current().copy()
        # Mantiene solo las que NO empiezan con guion bajo
        to_keep = [c for c in df.columns if not c.startswith('_')]
        dropped_count = len(df.columns) - len(to_keep)
        
        if dropped_count > 0:
            df = df[to_keep]
            add_log(f"Limpieza automática: Se eliminaron {dropped_count} variables temporales.")
            df_current.set(df)
            ui.notification_show(f"Limpieza lista: {dropped_count} columnas temporales eliminadas.", type="success")

    # --- Handler para resetear ---
    @reactive.Effect
    @reactive.event(input.reset_df)
    def _reset_df():
        df_current.set(df_original().copy())
        dtype_manual_state.set({})
        ops_log.set(["Dataset reseteado al original"])
        #ui.notification_show("Dataset devuelto a su estado original.", type="message")
