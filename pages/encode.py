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
            ui.div("PREVIEW", class_="card-title"),
            ui.HTML(build_df_preview_html(df)),
            class_="card"
        )
    )


def register_encode_handlers(input, output, df_current, add_log):
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
