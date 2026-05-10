"""Encoding page"""
from html import escape

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
            ui.div("COLUMNAS CATEGÓRICAS ACTUALES", class_="card-title"),
            ui.output_ui("encode_status"),
            class_="card"
        ),
        
        ui.div(
            ui.div("CONFIGURAR ENCODING", class_="card-title"),
            ui.div(
                ui.div(ui.input_select("enc_col", "Columna:", {**{"_all_": "— Todas categóricas —"}, **col_opts}), class_="ctrl-group"),
                ui.div(ui.input_select("enc_method", "Método:", {
                    "label": "Label Encoding",
                    "onehot": "One-Hot Encoding",
                    "ordinal": "Ordinal (manual)",
                    "binary": "Binary (0/1 si 2 únicos)",
                }), class_="ctrl-group"),
                class_="ctrl-row"
            ),
            ui.input_action_button("apply_encode", "Aplicar encoding", class_="btn btn-primary"),
            class_="card"
        ),

        ui.output_ui("ordinal_config"),

        ui.div(
            ui.div("PREVIEW", class_="card-title"),
            ui.HTML(build_df_preview_html(df.select_dtypes(include=["object"]))),
            class_="card"
        )
    )


def register_encode_handlers(input, output, df_current, add_log):
    """Register encoding page handlers"""
    saved_ordinal_order = reactive.Value("")
    ordinal_is_saved = reactive.Value(False)

    def _parsed_ordinal_order():
        return [item.strip() for item in input.ordinal_order().split(",") if item.strip()]
    
    @output
    @render.ui
    def ordinal_config():
        if input.enc_method() == "ordinal":
            return ui.div(
                ui.div("CONFIGURAR ORDINAL", class_="card-title"),
                ui.div(
                    ui.p("Ingrese el orden de las categorías separadas por comas"),
                    ui.input_text("ordinal_order", "Orden:", placeholder="cat1, cat2, cat3, ..."),
                    class_="ctrl-group"
                ),
                ui.output_ui("ordinal_order_table"),
                ui.output_ui("ordinal_save_button"),
                class_="card"
            )
        return ui.div()

    @output
    @render.ui
    def ordinal_save_button():
        if input.enc_method() != "ordinal":
            return ui.div()

        if ordinal_is_saved():
            label = "guardado"
            button_class = "btn btn-success"
        else:
            label = "Guardar orden"
            button_class = "btn btn-primary"

        return ui.input_action_button("save_ordinal_order", label, class_=button_class)

    @output
    @render.ui
    def ordinal_order_table():
        if input.enc_method() != "ordinal":
            return ui.div()

        if not ordinal_is_saved():
            return ui.div()

        order = [item.strip() for item in saved_ordinal_order().split(",") if item.strip()]
        if not order:
            return ui.div()
        
        df = df_current()
        enc_col = input.enc_col()
        if df is None or enc_col == "_all_" or enc_col not in df.columns:
            return ui.div()

        values = [str(value) for value in pd.unique(df[enc_col].dropna())]

        # enc_col == _all_ return (you must select a single variable)
        # df[enc_col].unique() 
        rows = "".join(
            f"<tr><td>{number}</td><td>{escape(value)}</td></tr>"
            for number, value in sorted(zip(order, values))
        )
        return ui.HTML(
            f"""
            <div class="df-table-wrap">
              <table class="df-table">
                <thead><tr><th>Valor</th><th>Orden</th></tr></thead>
                <tbody>{rows}</tbody>
              </table>
            </div>
            """
        )
    
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
            f"<tr><td>{c}</td><td>{df[c].nunique()}</td><td>{', '.join(str(v) for v in df[c].unique()[:25])}{'...' if df[c].nunique() > 25 else ''}</td></tr>"
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

    @reactive.Effect
    @reactive.event(input.apply_encode)
    def _apply_encode():
        df = df_current().copy()
        method = input.enc_method()
        col_sel = input.enc_col()
        cat_cols = get_cat_cols(df)
        cols = cat_cols if col_sel == "_all_" else [col_sel]

        for col in cols:
            if col not in df.columns:
                continue
            if method == "label":
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                add_log(f"Label encoding: '{col}'")
            elif method == "onehot":
                dummies = pd.get_dummies(df[col], prefix=col, drop_first=False).astype(int)
                df = pd.concat([df.drop(columns=[col]), dummies], axis=1)
                add_log(f"One-Hot encoding: '{col}' → {dummies.shape[1]} cols")
            elif method == "binary":
                if df[col].nunique() == 2:
                    vals = df[col].unique()
                    df[col] = df[col].map({vals[0]: 0, vals[1]: 1})
                    add_log(f"Binary encoding: '{col}'")
                else:
                    add_log(f"Binary encoding: '{col}' tiene {df[col].nunique()} únicos (se necesitan exactamente 2)")

        df_current.set(df)

    @reactive.Effect
    @reactive.event(input.save_ordinal_order)
    def _save_ordinal_order():
        if input.enc_method() != "ordinal":
            return

        order = _parsed_ordinal_order()
        if not order:
            add_log("Ordinal encoding: no se definió un orden válido")
            return

        saved_ordinal_order.set(", ".join(order))
        ordinal_is_saved.set(True)
        add_log(f"Ordinal encoding: orden guardado -> {saved_ordinal_order()}")

    @reactive.Effect
    def _reset_saved_state_on_change():
        if input.enc_method() != "ordinal":
            ordinal_is_saved.set(False)
            saved_ordinal_order.set("")
            return

        current_order = ", ".join(_parsed_ordinal_order())
        if current_order != saved_ordinal_order():
            ordinal_is_saved.set(False)
