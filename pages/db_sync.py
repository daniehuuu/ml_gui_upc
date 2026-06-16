"""DB sync page"""

from shiny import ui, reactive, render

def render_db_sync(df):
    """Renderiza la página para insertar nuevos datos a la BD"""
    if df is None:
        return ui.div("Primero carga o genera un dataset en Overview para sincronizarlo.", class_="alert alert-warning")
    
    return ui.div(
        ui.h2("Sincronización con Base de Datos ALDIMI"),
        ui.p("Inserta los datos actuales procesados en la base de datos central para futuros entrenamientos del modelo."),
        
        ui.div(
            ui.h4(f"Dataset actual listo para enviar: {df.shape[0]} filas"),
            ui.input_select(
                "target_table", 
                "Selecciona la tabla destino:",
                choices={"pacientes": "Tabla: Pacientes (Riesgo Clínico)", "inventario": "Tabla: Inventario (Logística)"}
            ),
            ui.input_action_button("append_to_db_btn", "Subir registros a la Base de Datos", class_="btn btn-primary mt-3"),
            class_="card p-4"
        )
    )

def register_db_sync_handlers(input, output, session, df_current, push_toast, add_log, connect_bd):
    @reactive.Effect
    @reactive.event(input.append_to_db_btn)
    def _():
        df = df_current()
        target = input.target_table()
        
        if df is None or df.empty:
            push_toast("No hay datos para guardar.", "error")
            return
            
        try:
            engine = connect_bd()
            # El secreto de la integración: if_exists='append'
            df.to_sql(name=target, con=engine, if_exists='append', index=False)
            
            push_toast(f"Se insertaron {len(df)} registros nuevos en la tabla '{target}'.", "success")
            add_log(f"Sincronización BD: {len(df)} filas añadidas a {target}.")
        except Exception as e:
            push_toast(f"Error al escribir en la base de datos.", "error")
            add_log(f"Error escritura BD ({target}): {str(e)}")