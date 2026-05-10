"""Classification modelling page"""
from shiny import ui, render, reactive
from app_helpers import get_num_cols

import time
import pandas as pd
import plotly.graph_objects as go
import random

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, classification_report, confusion_matrix
)
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE


def render_model(df):
    if df is None:
        return ui.div("Sin datos")

    num_cols = get_num_cols(df)

    return ui.div(
        ui.div(
            ui.tags.h2("Classification Modelling", class_="section-title"),
            ui.p("Random Forest Classifier con SMOTE y GridSearchCV", class_="section-sub")
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
        ),

        ui.div(
            ui.div("SIMULADOR EN VIVO (TEST SET)", class_="card-title"),
            ui.p("Toma un paciente aleatorio del conjunto de prueba (datos no vistos por el modelo) para validar su capacidad predictiva.", style="color: var(--muted);"),
            ui.input_action_button("btn_random_predict", "Predicción Aleatoria", class_="btn btn-primary"),
            ui.tags.br(), ui.tags.br(),
            ui.output_ui("random_prediction_ui"),
            class_="card"
        )
    )


def register_model_handlers(input, output, df_current, add_log, encoding_state):
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

        if target in features:
            features.remove(target)

        if not features:
            ui.notification_show("Debe seleccionar al menos una variable predictora.", type="error")
            return

        try:
            start_time = time.time()

            with ui.Progress(min=0, max=100) as p:
                p.set(5, message="🤖 Entrenando modelo... 5%", detail="Preparando datos")

                data = df[features + [target]].copy().dropna()
                X = data[features].copy()
                y = data[target].copy()

                cat_features = X.select_dtypes(include=["object", "category"]).columns.tolist()
                if cat_features:
                    ui.notification_show(
                        f"Hay variables categóricas sin encoding: {cat_features}. Pase primero por Encoding.",
                        type="error"
                    )
                    return

                p.set(20, message="🤖 Entrenando modelo... 20%", detail="Codificando variable objetivo")

                target_encoder = LabelEncoder()
                y_encoded = target_encoder.fit_transform(y.astype(str))
                class_names = list(target_encoder.classes_)

                p.set(35, message="🤖 Entrenando modelo... 35%", detail="Dividiendo datos en train/test")

                X_train, X_test, y_train, y_test = train_test_split(
                    X,
                    y_encoded,
                    test_size=0.2,
                    random_state=42,
                    stratify=y_encoded
                )

                p.set(50, message="🤖 Entrenando modelo... 50%", detail="Aplicando SMOTE al conjunto de entrenamiento")

                smote = SMOTE(random_state=42)
                X_train_res, y_train_res = smote.fit_resample(X_train, y_train)

                p.set(65, message="🤖 Entrenando modelo... 65%", detail="Ejecutando GridSearchCV. Esta etapa puede tardar varios minutos.")

                rf = RandomForestClassifier(random_state=42)

                param_grid = {
                    "n_estimators": [300, 500],
                    "max_depth": [10, 20, 30, None],
                    "min_samples_split": [2, 5],
                    "min_samples_leaf": [1, 2],
                    "max_features": ["sqrt", "log2"],
                    "class_weight": ["balanced", "balanced_subsample"]
                }

                grid = GridSearchCV(
                    estimator=rf,
                    param_grid=param_grid,
                    scoring="f1_macro",
                    cv=5,
                    n_jobs=-1,
                    verbose=2
                )

                grid.fit(X_train_res, y_train_res)

                p.set(85, message="🤖 Entrenando modelo... 85%", detail="Evaluando el mejor modelo")

                best_model = grid.best_estimator_
                y_pred = best_model.predict(X_test)

                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average="macro", zero_division=0)
                recall = recall_score(y_test, y_pred, average="macro", zero_division=0)
                f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

                report_dict = classification_report(
                    y_test,
                    y_pred,
                    target_names=class_names,
                    zero_division=0,
                    output_dict=True
                )

                cm = confusion_matrix(y_test, y_pred)

                fig = go.Figure(
                    data=go.Heatmap(
                        z=cm,
                        x=[f"Pred: {c}" for c in class_names],
                        y=[f"Real: {c}" for c in class_names],
                        text=cm,
                        texttemplate="%{text}",
                        textfont={"color": "white", "size": 14},
                        colorscale=[
                            [0.0, "rgba(20, 28, 52, 0.95)"],
                            [0.5, "rgba(0, 180, 160, 0.55)"],
                            [1.0, "rgba(0, 255, 200, 0.95)"]
                        ],
                        colorbar=dict(
                            title=dict(
                                text="Casos",
                                font=dict(color="white")
                            ),
                            tickfont=dict(color="white")
                        )
                    )
                )

                fig.update_layout(
                    title="Matriz de Confusión",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                    margin=dict(l=40, r=40, t=60, b=40),
                    height=420
                )

                cm_html = fig.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config={"displayModeBar": False}
                )

                importance_df = pd.DataFrame({
                    "Variable": features,
                    "Importancia": best_model.feature_importances_
                }).sort_values(by="Importancia", ascending=False)

                elapsed = int(time.time() - start_time)

                model_state.set({
                    "target": target,
                    "features": features,
                    "n_rows": data.shape[0],
                    "train_rows": len(y_train),
                    "test_rows": len(y_test),
                    "smote_rows": len(y_train_res),
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "best_params": grid.best_params_,
                    "report_dict": report_dict,
                    "cm_html": cm_html,
                    "importance_df": importance_df,
                    "elapsed": elapsed,
                    "best_model": best_model,
                    "X_test": X_test,
                    "y_test": y_test,
                    "class_names": class_names,
                })

                p.set(100, message="✅ Modelo entrenado 100%", detail=f"Resultados listos | Tiempo total: {elapsed}s")

            add_log(f"Random Forest entrenado con GridSearchCV | F1 Macro: {f1:.4f}")
            ui.notification_show("Modelo entrenado correctamente.", type="success")

        except Exception as e:
            add_log(f"Error en modelado: {str(e)}")
            ui.notification_show(f"Error al entrenar el modelo: {str(e)}", type="error")

    @output
    @render.ui
    def model_results():
        state = model_state()

        if state is None:
            return ui.p(
                "Aún no se ha entrenado ningún modelo.",
                style="color: var(--muted);"
            )

        metrics_html = f"""
        <div class="metric-grid">
            <div class="metric-card"><div class="metric-value">{state['accuracy']:.4f}</div><div class="metric-label">Accuracy</div></div>
            <div class="metric-card"><div class="metric-value">{state['precision']:.4f}</div><div class="metric-label">Precision Macro</div></div>
            <div class="metric-card"><div class="metric-value">{state['recall']:.4f}</div><div class="metric-label">Recall Macro</div></div>
            <div class="metric-card"><div class="metric-value">{state['f1']:.4f}</div><div class="metric-label">F1 Macro</div></div>
        </div>
        """

        params_html = "".join(
            f"<li><b>{k}</b>: {v}</li>" for k, v in state["best_params"].items()
        )

        importance_rows = "".join(
            f"<tr><td>{row['Variable']}</td><td>{row['Importancia']:.4f}</td></tr>"
            for _, row in state["importance_df"].iterrows()
        )

        report_rows = ""
        for label, values in state["report_dict"].items():
            if isinstance(values, dict):
                report_rows += f"""
                <tr>
                    <td>{label}</td>
                    <td>{values.get('precision', 0):.4f}</td>
                    <td>{values.get('recall', 0):.4f}</td>
                    <td>{values.get('f1-score', 0):.4f}</td>
                    <td>{values.get('support', 0):.0f}</td>
                </tr>
                """
            else:
                report_rows += f"""
                <tr>
                    <td>{label}</td>
                    <td colspan="3">{values:.4f}</td>
                    <td>-</td>
                </tr>
                """

        return ui.div(
            ui.HTML(metrics_html),

            ui.tags.h4("Resumen del entrenamiento", class_="model-subtitle"),
            ui.div(
                ui.p(f"Variable objetivo: {state['target']}"),
                ui.p(f"Registros usados: {state['n_rows']}"),
                ui.p(f"Entrenamiento: {state['train_rows']} registros"),
                ui.p(f"Prueba: {state['test_rows']} registros"),
                ui.p(f"Entrenamiento luego de SMOTE: {state['smote_rows']} registros"),
                ui.p(f"Tiempo total de entrenamiento: {state['elapsed']} segundos"),
                class_="model-info-box"
            ),

            ui.tags.h4("Mejores hiperparámetros", class_="model-subtitle"),
            ui.HTML(f"<div class='model-info-box'><ul>{params_html}</ul></div>"),

            ui.tags.h4("Matriz de confusión", class_="model-subtitle"),
            ui.HTML(state["cm_html"]),

            ui.tags.h4("Importancia de variables", class_="model-subtitle"),
            ui.HTML(f"""
                <table class="data-table">
                    <thead><tr><th>Variable</th><th>Importancia</th></tr></thead>
                    <tbody>{importance_rows}</tbody>
                </table>
            """),

            ui.tags.h4("Reporte de clasificación", class_="model-subtitle"),
            ui.HTML(f"""
                <table class="data-table classification-table">
                    <thead>
                        <tr>
                            <th>Clase / Métrica</th>
                            <th>Precision</th>
                            <th>Recall</th>
                            <th>F1-score</th>
                            <th>Support</th>
                        </tr>
                    </thead>
                    <tbody>
                        {report_rows}
                    </tbody>
                </table>
            """)
        )
    
    prediction_state = reactive.Value(None)

    # 2. Lógica al presionar el botón "Predicción Aleatoria"
    @reactive.Effect
    @reactive.event(input.btn_random_predict)
    def _do_random_predict():
        state = model_state()
        if state is None or "best_model" not in state:
            ui.notification_show("Primero debes entrenar el modelo.", type="warning")
            return
        
        X_test = state["X_test"]
        y_test = state["y_test"]
        best_model = state["best_model"]
        target_col = input.target_col()

        # Seleccionar un paciente aleatorio
        random_idx = random.randint(0, len(X_test) - 1)
        
        # Extraer la fila de datos (X)
        sample_X = X_test.iloc[[random_idx]]
        
        # Extraer el valor real (y). Manejo seguro por si y_test es Serie o Array
        true_y_encoded = y_test.iloc[random_idx] if isinstance(y_test, pd.Series) else y_test[random_idx]
        
        # Hacer la predicción con el modelo
        pred_encoded = best_model.predict(sample_X)[0]
        probs = best_model.predict_proba(sample_X)[0]

        encodings = encoding_state()

        true_label_text = decode_value(int(true_y_encoded), target_col, encodings)
        pred_label_text = decode_value(int(pred_encoded), target_col, encodings)
        
        prediction_state.set({
            "features_dict": sample_X.iloc[0].round(4).to_dict(),
            "true_label": true_label_text,
            "pred_label": pred_label_text,
            "confidence": round(max(probs) * 100, 2)
        })


    @output
    @render.ui
    def random_prediction_ui():
        p_state = prediction_state()
        if p_state is None:
            return ui.div()
            
        true_label = p_state["true_label"]
        pred_label = p_state["pred_label"]
        
        # Lógica exacta basada en las clases manuales
        pred_str = str(pred_label).strip().lower()

        # Lógica dinámica: Busca las palabras clave sin importar el número interno
        if pred_label == "1" or "low" in pred_str:
            bg_color = "#f0fdf4" 
            border_color = "#22c55e" 
            status_icon = f"✅ BAJO RIESGO ({pred_label})"
            accion_clinica = "Paciente pediátrico fuera de peligro inmediato. Mantener controles de rutina y nutrición en las instalaciones de ALDIMI."
            
        elif pred_label == "2" or "medium" in pred_str:
            bg_color = "#fffbeb" 
            border_color = "#f59e0b" 
            status_icon = f"⚠️ RIESGO MODERADO ({pred_label})"
            accion_clinica = "El paciente requiere entrar en observación preventiva. Programar una consulta con endocrinología pediátrica en el corto plazo."
            
        elif pred_label == "0" or "high" in pred_str:
            bg_color = "#fef2f2" 
            border_color = "#ef4444" 
            status_icon = f"🚨 ALERTA CRÍTICA: ALTO RIESGO ({pred_label})"
            accion_clinica = "Derivación hospitalaria urgente. Iniciar protocolo de traslado a centro oncológico pediátrico para atención prioritaria."

        else:
            # Fallback dinámico para CUALQUIER otro dataset que entrenen
            bg_color = "#f3f4f6"
            border_color = "#9ca3af"
            status_icon = f"ℹ️ CLASIFICACIÓN: {pred_label.upper()}"
            accion_clinica = "Resultado de clasificación genérica. Aplicar protocolo estándar según la clase obtenida."

        # Identificador visual si el modelo acertó o se equivocó (True Positive vs False Positive/Negative)
        match_icon = "🎯 ACIERTO DEL MODELO" if true_label == pred_label else "❌ FALLO DE PREDICCIÓN"
        match_color = "#16a34a" if true_label == pred_label else "#dc2626"

        # Crear la lista de variables para mostrar qué evaluó el modelo
        features_html = "".join(
            f"<li><b>{k}</b>: {v}</li>" for k, v in p_state["features_dict"].items()
        )

        return ui.HTML(f"""
            <div style="display: flex; gap: 20px;">
                <div style="flex: 1; padding: 15px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <h4 style="margin-top: 0; color: var(--muted); display: flex; justify-content: space-between;">
                        <span>Biomarcadores Evaluados</span>
                        <span style="color: {match_color}; font-size: 0.8em; border: 1px solid {match_color}; padding: 2px 6px; border-radius: 4px;">
                            {match_icon} (Real: {true_label})
                        </span>
                    </h4>
                    <ul style="font-size: 0.9em; column-count: 2; list-style-type: none; padding-left: 0;">
                        {features_html}
                    </ul>
                </div>
                
                <div style="flex: 1; padding: 15px; background: {bg_color}; border-radius: 8px; border-left: 6px solid {border_color};">
                    <h4 style="margin-top: 0; color: {border_color}; font-size: 1.2em;">{status_icon}</h4>
                    <p style="margin-bottom: 8px;">
                        <strong>Confianza del Algoritmo:</strong> <span style="font-size: 1.1em;">{p_state['confidence']}%</span>
                    </p>
                    <hr style="border-top: 1px solid {border_color}; opacity: 0.3; margin: 10px 0;">
                    <p style="margin-bottom: 0; font-size: 1.05em; line-height: 1.4;">
                        <strong>Protocolo ALDIMI:</strong><br>
                        {accion_clinica}
                    </p>
                </div>
            </div>
        """)
    
def decode_value(encoded_val, col_name, encodings):

    if col_name not in encodings:
        return str(encoded_val)  # fallback
    
    mapping = encodings[col_name]
    
    # Caso Label/Binary
    if isinstance(mapping, dict):
        inv_map = {v: k for k, v in mapping.items()}
        return inv_map.get(encoded_val, str(encoded_val))
    
    # Caso One-Hot (lista de columnas dummy)
    elif isinstance(mapping, list):
        # reconstruir categoría original
        for dummy_col in mapping:
            if encoded_val.get(dummy_col, 0) == 1:
                return dummy_col.replace("_encoded", "").replace(f"{col_name}_", "")
        return str(encoded_val)
    
    return str(encoded_val)