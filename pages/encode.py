"""Encoding page"""
from shiny import ui, render, reactive
from sklearn.preprocessing import LabelEncoder
import pandas as pd
from app_helpers import (
    df_preview_html as build_df_preview_html,
    get_cat_cols,
)


def render_encode(df):
    """Render the encoding page"""
    if df is None:
        return ui.div("Sin datos")
    cat_cols = get_cat_cols(df)
    if not cat_cols:
        return ui.div(
            ui.div(ui.tags.h2("Encoding", class_="section-title"),
                   ui.p("Codificación de variables categóricas", class_="section-sub")),
            ui.div("No hay columnas categóricas disponibles.", class_="card")
        )

    col_opts = {c: f"{c} ({df[c].nunique()} únicos)" for c in cat_cols}

    return ui.div(
        ui.div(ui.tags.h2("Encoding", class_="section-title"),
               ui.p("Codificación de variables categóricas", class_="section-sub")),

        ui.div(
            ui.div("CONFIGURAR ENCODING", class_="card-title"),
            ui.div(
                ui.div(ui.input_select("enc_col", "Columna:", {**{"_all_": "— Todas categóricas —"}, **col_opts}), class_="ctrl-group"),
                ui.div(ui.input_select("enc_method", "Método:", {
                    "label": "Label Encoding",
                    "onehot": "One-Hot Encoding",
                    "ordinal": "Ordinal (manual no disp.)",
                    "binary": "Binary (0/1 si 2 únicos)",
                }), class_="ctrl-group"),
                class_="ctrl-row"
            ),
            ui.input_action_button("apply_encode", "Aplicar encoding", class_="btn btn-primary"),
            class_="card"
        ),

        ui.div(
            ui.div("COLUMNAS CATEGÓRICAS ACTUALES", class_="card-title"),
            ui.output_ui("encode_status"),
            class_="card"
        ),

        ui.div(
            ui.div("DICCIONARIO DE ENCODING (MEMORIA GLOBAL)", class_="card-title"),
            ui.p("Estos mapeos se guardan en memoria para asegurar que las futuras predicciones respeten el mismo formato.", style="color: var(--muted); font-size: 0.9em;"),
            ui.output_ui("encoding_dictionary_ui"),
            class_="card"
        ),

        ui.div(
            ui.div("PREVIEW", class_="card-title"),
            ui.HTML(build_df_preview_html(df)),
            class_="card"
        )
    )


def register_encode_handlers(input, output, df_current, add_log, encoding_state):
    """Register encoding page handlers"""
    
    @output
    @render.ui
    def encode_status():
        df = df_current()
        if df is None:
            return ui.div()
        cat_cols = get_cat_cols(df)
        if not cat_cols:
            return ui.HTML('<span style="color:var(--accent)">✓ Sin columnas categóricas</span>')
        rows = "".join(
            f"<tr><td>{c}</td><td>{df[c].nunique()}</td><td>{', '.join(str(v) for v in df[c].unique()[:5])}{'...' if df[c].nunique() > 5 else ''}</td></tr>"
            for c in cat_cols
        )
        return ui.HTML(f"""
        <div class="df-table-wrap">
          <table class="df-table">
            <thead><tr><th>Columna</th><th>Únicos</th><th>Valores</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """)
    
    @output
    @render.ui
    def encoding_dictionary_ui():
        current_dict = encoding_state()
        if not current_dict:
            return ui.div("El diccionario está vacío. Aplica Label o Binary Encoding para empezar a registrar.", style="font-style: italic; color: gray;")
            
        dict_html = ""
        for col, mapping in current_dict.items():
            # Construye los tags para mostrar "Femenino: 0", "Masculino: 1"
            map_str = "".join(f"<span class='pill' style='margin-right: 5px; background: #e2e8f0; color: #333;'>{k} = <b>{v}</b></span>" for k, v in mapping.items())
            dict_html += f"<div style='margin-bottom: 10px;'><strong>{col}:</strong><br>{map_str}</div>"
            
        return ui.HTML(dict_html)

    @reactive.Effect
    @reactive.event(input.apply_encode)
    def _apply_encode():
        df = df_current().copy()
        method = input.enc_method()
        col_sel = input.enc_col()
        cat_cols = get_cat_cols(df)
        
        if not cat_cols and col_sel == "_all_":
            ui.notification_show("No hay variables categóricas.", type="warning")
            return

        cols = cat_cols if col_sel == "_all_" else [col_sel]
        
        # Recuperamos el diccionario global actual para no borrar lo que ya estaba
        current_encoding_dict = encoding_state().copy()

        for col in cols:
            if col not in df.columns: continue
            
            # 1. LÓGICA LABEL ENCODER (Guarda el mapeo automático)
            if method == "label":
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                mapping = {str(class_name): int(i) for i, class_name in enumerate(le.classes_)}
                current_encoding_dict[col] = mapping 
                
                add_log(f"Label encoding aplicado a '{col}'")
                
            # 2. LÓGICA BINARY (Guarda el mapeo 0 y 1)
            elif method == "binary":
                if df[col].nunique() == 2:
                    vals = list(df[col].unique())
                    mapping = {str(vals[0]): 0, str(vals[1]): 1}
                    df[col] = df[col].map(mapping)
                    current_encoding_dict[col] = mapping 
                    add_log(f"Binary encoding aplicado a '{col}'")
                else:
                    ui.notification_show(f"'{col}' tiene {df[col].nunique()} valores. Binary exige exactamente 2.", type="error")
                    
            elif method == "onehot":
                dummies = pd.get_dummies(df[col], prefix=col, drop_first=False).astype(int)
                dummies.columns = [f"{c}_encoded" for c in dummies.columns]
                df = pd.concat([df, dummies], axis=1)
                df.rename(columns={col: f"_{col}"}, inplace=True)
                add_log(f"One-Hot encoding: '{col}' expandida a {dummies.shape[1]} variables.")

        # Guardamos todo en memoria global
        encoding_state.set(current_encoding_dict)
        df_current.set(df)
        ui.notification_show(f"Encoding '{method}' aplicado correctamente.", type="success")