"""Modelling page: Classification + Linear Regression"""
from shiny import ui, render, reactive
from app_helpers import get_num_cols

import time
import random
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE


def render_model(df):
    """Render modelling page"""
    if df is None:
        return ui.div("Sin datos")

    num_cols = get_num_cols(df)

    return ui.div(
        ui.div(
            ui.tags.h2("Modelling", class_="section-title"),
            ui.p(
                "Entrenamiento de modelos supervisados: clasificación y regresión lineal",
                class_="section-sub"
            )
        ),

        ui.div(
            ui.div("CONFIGURACIÓN DEL MODELO", class_="card-title"),

            ui.input_select(
                "problem_type",
                "Tipo de problema:",
                choices={
                    "classification": "Clasificación - Random Forest Classifier",
                    "regression": "Regresión - Regresión Lineal"
                },
                selected="classification"
            ),

            ui.tags.br(),

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
                "Entrenar modelo",
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
            ui.p(
                "Toma un registro aleatorio del conjunto de prueba para validar la predicción con datos no vistos por el modelo.",
                style="color: var(--muted);"
            ),
            ui.input_action_button(
                "btn_random_predict",
                "Predicción aleatoria",
                class_="btn btn-primary"
            ),
            ui.tags.br(),
            ui.tags.br(),
            ui.output_ui("random_prediction_ui"),
            class_="card"
        )
    )


def register_model_handlers(input,output,df_current,add_log,encoding_state,classification_model_state,regression_model_state):
    """Register modelling page handlers"""

    model_state = reactive.Value(None)
    prediction_state = reactive.Value(None)

    def decode_value(encoded_value, target_col, encodings, class_names=None):
        """
        Intenta decodificar valores codificados.
        Sirve para targets que fueron transformados con Label/Binary Encoding.
        """
        value_str = str(encoded_value)

        if class_names is not None:
            try:
                value_str = str(class_names[int(encoded_value)])
            except Exception:
                value_str = str(encoded_value)

        if target_col in encodings:
            reverse_map = {str(v): str(k) for k, v in encodings[target_col].items()}
            return reverse_map.get(value_str, value_str)

        return value_str

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

        problem_type = input.problem_type()
        target = input.target_col()
        features = list(input.feature_cols())

        if target in features:
            features.remove(target)

        if not target:
            ui.notification_show("Debe seleccionar una variable objetivo.", type="error")
            return

        if not features:
            ui.notification_show("Debe seleccionar al menos una variable predictora.", type="error")
            return

        if problem_type == "classification":
            train_classification_model(df, target, features)
        elif problem_type == "regression":
            train_regression_model(df, target, features)

    def train_classification_model(df, target, features):
        """Train Random Forest Classifier with optional SMOTE and GridSearchCV"""
        try:
            start_time = time.time()

            with ui.Progress(min=0, max=100) as p:
                p.set(5, message="🤖 Entrenando clasificación... 5%", detail="Preparando datos")

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

                if data.empty:
                    ui.notification_show("No hay datos disponibles luego de eliminar nulos.", type="error")
                    return

                p.set(20, message="🤖 Entrenando clasificación... 20%", detail="Codificando variable objetivo")

                target_encoder = LabelEncoder()
                y_encoded = target_encoder.fit_transform(y.astype(str))
                class_names = list(target_encoder.classes_)

                class_counts = pd.Series(y_encoded).value_counts()
                if len(class_counts) < 2:
                    ui.notification_show("La variable objetivo necesita al menos 2 clases.", type="error")
                    return

                p.set(35, message="🤖 Entrenando clasificación... 35%", detail="Dividiendo train/test")

                X_train, X_test, y_train, y_test = train_test_split(
                    X,
                    y_encoded,
                    test_size=0.2,
                    random_state=42,
                    stratify=y_encoded
                )

                p.set(50, message="🤖 Entrenando clasificación... 50%", detail="Aplicando SMOTE si es posible")

                train_class_counts = pd.Series(y_train).value_counts()
                min_class_count = train_class_counts.min()

                if min_class_count >= 2:
                    k_neighbors = min(5, min_class_count - 1)
                    smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
                    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
                    smote_applied = True
                else:
                    X_train_res, y_train_res = X_train, y_train
                    smote_applied = False

                p.set(65, message="🤖 Entrenando clasificación... 65%", detail="Ejecutando GridSearchCV")

                rf = RandomForestClassifier(random_state=42)

                param_grid = {
                    "n_estimators": [200, 300],
                    "max_depth": [10, 20, None],
                    "min_samples_split": [2, 5],
                    "min_samples_leaf": [1, 2],
                }

                grid = GridSearchCV(
                    estimator=rf,
                    param_grid=param_grid,
                    scoring="f1_macro",
                    cv=5,
                    n_jobs=-1,
                    verbose=True
                )

                grid.fit(X_train_res, y_train_res)

                p.set(85, message="🤖 Entrenando clasificación... 85%", detail="Evaluando modelo")

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
                        colorbar=dict(title=dict(text="Casos", font=dict(color="white")))
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
                    "problem_type": "classification",
                    "target": target,
                    "features": features,
                    "n_rows": data.shape[0],
                    "train_rows": len(y_train),
                    "test_rows": len(y_test),
                    "smote_rows": len(y_train_res),
                    "smote_applied": smote_applied,
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

                classification_model_state.set({
                    "problem_type": "classification",
                    "target": target,
                    "features": features,
                    "best_model": best_model,
                    "class_names": class_names,
                    "target_encoder": target_encoder,
                    "encoding_state": encoding_state(),
                    "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                })

                add_log(f"Modelo global de clasificación guardado: {target} | Features: {len(features)}")

                prediction_state.set(None)

                p.set(100, message="✅ Clasificación entrenada 100%", detail=f"Tiempo total: {elapsed}s")

            add_log(f"Random Forest Classifier entrenado | F1 Macro: {f1:.4f}")
            ui.notification_show("Modelo de clasificación entrenado correctamente.", type="success")

        except Exception as e:
            add_log(f"Error en clasificación: {str(e)}")
            ui.notification_show(f"Error al entrenar clasificación: {str(e)}", type="error")

    def train_regression_model(df, target, features):
        """Train Linear Regression model"""
        try:
            start_time = time.time()

            with ui.Progress(min=0, max=100) as p:
                p.set(10, message="📈 Entrenando regresión lineal... 10%", detail="Preparando datos")

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

                if not pd.api.types.is_numeric_dtype(y):
                    ui.notification_show(
                        "Para regresión, la variable objetivo debe ser numérica.",
                        type="error"
                    )
                    return

                if data.empty:
                    ui.notification_show("No hay datos disponibles luego de eliminar nulos.", type="error")
                    return

                p.set(35, message="📈 Entrenando regresión lineal... 35%", detail="Dividiendo train/test")

                X_train, X_test, y_train, y_test = train_test_split(
                    X,
                    y,
                    test_size=0.2,
                    random_state=42
                )

                p.set(60, message="📈 Entrenando regresión lineal... 60%", detail="Ajustando modelo")

                model = LinearRegression()
                model.fit(X_train, y_train)

                p.set(80, message="📈 Entrenando regresión lineal... 80%", detail="Evaluando modelo")

                y_pred = model.predict(X_test)

                mae = mean_absolute_error(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                r2 = r2_score(y_test, y_pred)

                coef_df = pd.DataFrame({
                    "Variable": features,
                    "Coeficiente": model.coef_
                }).sort_values(by="Coeficiente", ascending=False)

                intercept = model.intercept_

                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=y_test,
                    y=y_pred,
                    mode="markers",
                    name="Predicciones",
                    marker=dict(size=7, opacity=0.7)
                ))

                min_val = min(float(np.min(y_test)), float(np.min(y_pred)))
                max_val = max(float(np.max(y_test)), float(np.max(y_pred)))

                fig.add_trace(go.Scatter(
                    x=[min_val, max_val],
                    y=[min_val, max_val],
                    mode="lines",
                    name="Predicción perfecta",
                    line=dict(dash="dash")
                ))

                fig.update_layout(
                    title="Valores reales vs predichos",
                    xaxis_title="Valor real",
                    yaxis_title="Valor predicho",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                    margin=dict(l=40, r=40, t=60, b=40),
                    height=420
                )

                reg_plot_html = fig.to_html(
                    full_html=False,
                    include_plotlyjs=False,
                    config={"displayModeBar": False}
                )

                elapsed = int(time.time() - start_time)

                model_state.set({
                    "problem_type": "regression",
                    "target": target,
                    "features": features,
                    "n_rows": data.shape[0],
                    "train_rows": len(y_train),
                    "test_rows": len(y_test),
                    "mae": mae,
                    "rmse": rmse,
                    "r2": r2,
                    "coef_df": coef_df,
                    "intercept": intercept,
                    "reg_plot_html": reg_plot_html,
                    "elapsed": elapsed,
                    "best_model": model,
                    "X_test": X_test,
                    "y_test": y_test,
                    "y_pred": y_pred,
                })

                regression_model_state.set({
                    "problem_type": "regression",
                    "target": target,
                    "features": features,
                    "best_model": model,
                    "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                })

                prediction_state.set(None)

                p.set(100, message="✅ Regresión lineal entrenada 100%", detail=f"Tiempo total: {elapsed}s")

            add_log(f"Regresión Lineal entrenada | MAE: {mae:.4f} | RMSE: {rmse:.4f} | R²: {r2:.4f}")
            ui.notification_show("Modelo de regresión lineal entrenado correctamente.", type="success")

        except Exception as e:
            add_log(f"Error en regresión lineal: {str(e)}")
            ui.notification_show(f"Error al entrenar regresión lineal: {str(e)}", type="error")

    @output
    @render.ui
    def model_results():
        state = model_state()

        if state is None:
            return ui.p(
                "Aún no se ha entrenado ningún modelo.",
                style="color: var(--muted);"
            )

        if state["problem_type"] == "classification":
            return render_classification_results(state)

        if state["problem_type"] == "regression":
            return render_regression_results(state)

        return ui.div("Tipo de modelo no reconocido.")

    def render_classification_results(state):
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

        smote_text = "Sí" if state["smote_applied"] else "No"

        return ui.div(
            ui.HTML(metrics_html),

            ui.tags.h4("Resumen del entrenamiento", class_="model-subtitle"),
            ui.div(
                ui.p(f"Tipo de modelo: Random Forest Classifier"),
                ui.p(f"Variable objetivo: {state['target']}"),
                ui.p(f"Registros usados: {state['n_rows']}"),
                ui.p(f"Entrenamiento: {state['train_rows']} registros"),
                ui.p(f"Prueba: {state['test_rows']} registros"),
                ui.p(f"SMOTE aplicado: {smote_text}"),
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

    def render_regression_results(state):
        metrics_html = f"""
        <div class="metric-grid">
            <div class="metric-card"><div class="metric-value">{state['mae']:.4f}</div><div class="metric-label">MAE</div></div>
            <div class="metric-card"><div class="metric-value">{state['rmse']:.4f}</div><div class="metric-label">RMSE</div></div>
            <div class="metric-card"><div class="metric-value">{state['r2']:.4f}</div><div class="metric-label">R²</div></div>
        </div>
        """

        coef_rows = "".join(
            f"<tr><td>{row['Variable']}</td><td>{row['Coeficiente']:.6f}</td></tr>"
            for _, row in state["coef_df"].iterrows()
        )

        return ui.div(
            ui.HTML(metrics_html),

            ui.tags.h4("Resumen del entrenamiento", class_="model-subtitle"),
            ui.div(
                ui.p("Tipo de modelo: Regresión Lineal Múltiple"),
                ui.p(f"Variable objetivo: {state['target']}"),
                ui.p(f"Registros usados: {state['n_rows']}"),
                ui.p(f"Entrenamiento: {state['train_rows']} registros"),
                ui.p(f"Prueba: {state['test_rows']} registros"),
                ui.p(f"Intercepto: {state['intercept']:.6f}"),
                ui.p(f"Tiempo total de entrenamiento: {state['elapsed']} segundos"),
                class_="model-info-box"
            ),

            ui.tags.h4("Valores reales vs predichos", class_="model-subtitle"),
            ui.HTML(state["reg_plot_html"]),

            ui.tags.h4("Coeficientes del modelo", class_="model-subtitle"),
            ui.HTML(f"""
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Variable</th>
                            <th>Coeficiente</th>
                        </tr>
                    </thead>
                    <tbody>
                        {coef_rows}
                    </tbody>
                </table>
            """),

            ui.div(
                ui.p(
                    "Interpretación: un coeficiente positivo indica que, manteniendo las demás variables constantes, "
                    "el aumento de esa variable se asocia con un incremento en la variable objetivo. "
                    "Un coeficiente negativo indica una asociación inversa.",
                    style="color: var(--muted); margin-top: 10px;"
                ),
                class_="model-info-box"
            )
        )

    @reactive.Effect
    @reactive.event(input.btn_random_predict)
    def _do_random_predict():
        state = model_state()

        if state is None or "best_model" not in state:
            ui.notification_show("Primero debes entrenar el modelo.", type="warning")
            return

        if state["problem_type"] == "classification":
            random_classification_prediction(state)
        elif state["problem_type"] == "regression":
            random_regression_prediction(state)

    def random_classification_prediction(state):
        X_test = state["X_test"]
        y_test = state["y_test"]
        best_model = state["best_model"]
        target_col = state["target"]
        class_names = state["class_names"]

        random_idx = random.randint(0, len(X_test) - 1)
        sample_X = X_test.iloc[[random_idx]]

        true_y_encoded = y_test.iloc[random_idx] if isinstance(y_test, pd.Series) else y_test[random_idx]
        pred_encoded = best_model.predict(sample_X)[0]
        probs = best_model.predict_proba(sample_X)[0]

        encodings = encoding_state()

        true_label_text = decode_value(true_y_encoded, target_col, encodings, class_names)
        pred_label_text = decode_value(pred_encoded, target_col, encodings, class_names)

        prediction_state.set({
            "problem_type": "classification",
            "features_dict": sample_X.iloc[0].round(4).to_dict(),
            "true_label": true_label_text,
            "pred_label": pred_label_text,
            "confidence": round(max(probs) * 100, 2)
        })

    def random_regression_prediction(state):
        X_test = state["X_test"]
        y_test = state["y_test"]
        best_model = state["best_model"]

        random_idx = random.randint(0, len(X_test) - 1)
        sample_X = X_test.iloc[[random_idx]]

        true_value = y_test.iloc[random_idx] if isinstance(y_test, pd.Series) else y_test[random_idx]
        pred_value = best_model.predict(sample_X)[0]
        abs_error = abs(true_value - pred_value)

        prediction_state.set({
            "problem_type": "regression",
            "features_dict": sample_X.iloc[0].round(4).to_dict(),
            "true_value": round(float(true_value), 4),
            "pred_value": round(float(pred_value), 4),
            "abs_error": round(float(abs_error), 4)
        })

    @output
    @render.ui
    def random_prediction_ui():
        p_state = prediction_state()

        if p_state is None:
            return ui.div()

        if p_state["problem_type"] == "classification":
            return render_random_classification_prediction(p_state)

        if p_state["problem_type"] == "regression":
            return render_random_regression_prediction(p_state)

        return ui.div()

    def render_random_classification_prediction(p_state):
        true_label = p_state["true_label"]
        pred_label = p_state["pred_label"]
        confidence = p_state["confidence"]

        is_correct = str(true_label) == str(pred_label)
        status_text = "Correcto" if is_correct else "Incorrecto"
        status_color = "var(--accent)" if is_correct else "var(--accent2)"

        feature_rows = "".join(
            f"<tr><td>{k}</td><td>{v}</td></tr>"
            for k, v in p_state["features_dict"].items()
        )

        return ui.HTML(f"""
            <div class="model-info-box">
                <h4 style="color:{status_color};">Resultado: {status_text}</h4>
                <p><b>Valor real:</b> {true_label}</p>
                <p><b>Predicción:</b> {pred_label}</p>
                <p><b>Confianza:</b> {confidence}%</p>
            </div>

            <h4 class="model-subtitle">Variables del registro evaluado</h4>
            <table class="data-table">
                <thead>
                    <tr><th>Variable</th><th>Valor</th></tr>
                </thead>
                <tbody>
                    {feature_rows}
                </tbody>
            </table>
        """)

    def render_random_regression_prediction(p_state):
        feature_rows = "".join(
            f"<tr><td>{k}</td><td>{v}</td></tr>"
            for k, v in p_state["features_dict"].items()
        )

        return ui.HTML(f"""
            <div class="model-info-box">
                <h4 style="color:var(--accent);">Predicción de regresión lineal</h4>
                <p><b>Valor real:</b> {p_state['true_value']}</p>
                <p><b>Valor predicho:</b> {p_state['pred_value']}</p>
                <p><b>Error absoluto:</b> {p_state['abs_error']}</p>
            </div>

            <h4 class="model-subtitle">Variables del registro evaluado</h4>
            <table class="data-table">
                <thead>
                    <tr><th>Variable</th><th>Valor</th></tr>
                </thead>
                <tbody>
                    {feature_rows}
                </tbody>
            </table>
        """)