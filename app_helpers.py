from html import escape

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import shapiro
from shiny import ui
from scipy.stats import gaussian_kde

separator_options = {
    ",": "Coma ( , )",
    ";": "Punto y coma ( ; )",
    "\t": "Tab",
    "custom": "Personalizado",
}

missing_categories = [
    (0, 0.01, "Trivial", "var(--accent)", "< 1%"),
    (0.01, 0.05, "Manejable", "#7c8cf8", "[1%, 5%)"),
    (0.05, 0.15, "Sofisticado", "#f59e0b", "[5%, 15%)"),
    (0.15, 1.0, "Perjudicial", "var(--accent2)", "> 15%"),
]


def read_csv_dataset(file_path, separator, header, encoding):
    last_error = None
    for trial_encoding in [encoding, "utf-8", "latin1"]:
        try:
            df = pd.read_csv(
                file_path,
                sep=separator,
                header=header,
                encoding=trial_encoding,
                engine="python",
            )
            return df, trial_encoding, None
        except Exception as exc:
            last_error = exc
    return None, None, last_error


def html_figure(fig, height=420):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=24, r=24, t=40, b=24),
        height=height,
        font=dict(family="JetBrains Mono, monospace", color="#e8eaf2"),
    )
    return ui.HTML(fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False}))


def missing_category_for_pct(pct):
    for low, high, label, color, _ in missing_categories:
        if low <= pct < high:
            return label, color
    return "Perjudicial", "var(--accent2)"


def outlier_category_for_pct(pct):
    if pct == 0:
        return "Sin outliers", "var(--accent)"
    if pct < 1:
        return "Leve", "var(--accent)"
    if pct < 5:
        return "Moderado", "#7c8cf8"
    if pct < 15:
        return "Alto", "#f59e0b"
    return "Crítico", "var(--accent2)"


def get_num_cols(df):
    return df.select_dtypes(include=np.number).columns.tolist()


def get_cat_cols(df):
    return df.select_dtypes(include="object").columns.tolist()


def df_preview_html(df, max_rows=8, just_encoded=False):
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    
    if just_encoded:
        encoded_cols = [col for col in df.columns if str(col).endswith("_encoded")]
        if not encoded_cols:
            return "<div style='color:var(--muted);font-style:italic;'>No se han aplicado encodings aún</div>"
        cols_to_display = encoded_cols
        num_cols = [col for col in encoded_cols if col in num_cols]
    else:
        cols_to_display = df.columns.tolist()
    
    rows = []
    for _, row in df.head(max_rows).iterrows():
        cells = []
        for col in cols_to_display:
            val = row[col]
            if pd.isna(val):
                cells.append("<td class='null-cell'>NaN</td>")
            elif col in num_cols:
                cells.append(f"<td class='num-cell'>{escape(str(val))}</td>")
            else:
                cells.append(f"<td>{escape(str(val))}</td>")
        rows.append(f"<tr>{''.join(cells)}</tr>")
    headers = "".join(f"<th>{escape(str(c))}</th>" for c in cols_to_display)
    return f"""
    <div class="df-table-wrap">
      <table class="df-table">
        <thead><tr>{headers}</tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    <div style="color:var(--muted);font-size:11px;margin-top:6px;">
      Mostrando {min(max_rows, len(df))} de {len(df)} filas · {len(cols_to_display)} columnas
    </div>
    """

def df_preview_html_encoded(df, max_rows=8):
    return df_preview_html(df, max_rows, just_encoded=True)  

def missing_report_html(df):
    rows = []
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        missing_pct = round(100 * missing_count / len(df), 2) if len(df) else 0
        category, color = missing_category_for_pct(missing_pct / 100 if missing_pct else 0)
        rows.append(
            f"<tr><td>{escape(str(col))}</td><td>{missing_count}</td><td>{missing_pct}%</td><td><span class='pill' style='background:{color};color:#fff'>{category}</span></td></tr>"
        )
    legend = "".join(
        f"<div class='legend-item'><span class='legend-swatch' style='background:{color}'></span><div><strong>{label}</strong><div style='color:var(--muted)'>{range_text}</div></div></div>"
        for _, _, label, color, range_text in missing_categories
    )
    return f"""
    <div class="df-table-wrap">
      <table class="df-table">
        <thead><tr><th>Columna</th><th>Nulos</th><th>%</th><th>Categoría</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    <div class="legend-grid">{legend}</div>
    """


def outlier_report_html(df, method="iqr", z_threshold=3.0):
    num_cols = get_num_cols(df)
    rows = []
    for col in num_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        if method == "zscore":
            mean = series.mean()
            std = series.std(ddof=0) or 1
            outliers = ((series - mean).abs() > z_threshold * std).sum()
            method_label = f"Z-score ±{z_threshold}σ"
        else:
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = ((series < lower) | (series > upper)).sum()
            method_label = "IQR"
        pct = round(100 * outliers / len(series), 2)
        category, color = outlier_category_for_pct(pct)
        rows.append(
            f"<tr><td>{escape(str(col))}</td><td>{outliers}</td><td>{pct}%</td><td><span class='pill' style='background:{color};color:#fff'>{category}</span></td><td>{method_label}</td></tr>"
        )
    legend = """
    <div class="legend-grid">
      <div class="legend-item"><span class="legend-swatch" style="background:var(--accent)"></span><div><strong>Leve</strong><div style="color:var(--muted)">&lt; 1%</div></div></div>
      <div class="legend-item"><span class="legend-swatch" style="background:#7c8cf8"></span><div><strong>Moderado</strong><div style="color:var(--muted)">[1%, 5%)</div></div></div>
      <div class="legend-item"><span class="legend-swatch" style="background:#f59e0b"></span><div><strong>Alto</strong><div style="color:var(--muted)">[5%, 15%)</div></div></div>
      <div class="legend-item"><span class="legend-swatch" style="background:var(--accent2)"></span><div><strong>Crítico</strong><div style="color:var(--muted)">&gt;= 15%</div></div></div>
    </div>
    """
    return f"""
    <div class="df-table-wrap">
      <table class="df-table">
        <thead><tr><th>Columna</th><th>Outliers</th><th>%</th><th>Categoría</th><th>Método</th></tr></thead>
        <tbody>{''.join(rows) if rows else '<tr><td colspan="5">Sin columnas numéricas</td></tr>'}</tbody>
      </table>
    </div>
    {legend}
    """


def make_corr_heatmap(df, columns, method):
    corr = df[columns].corr(method=method)
    fig = px.imshow(
        corr,
        text_auto='.4f',
        color_continuous_scale=[[0, "#EAE3F1"], [0.5, "#9966CC"], [1, "#66CC99"]],
        zmin=-1,
        zmax=1,
        aspect="auto",
    )
    fig.update_layout(title=f"Matriz de correlación ({method.title()})")
    return fig

def make_cov_heatmap(df, columns):
    """Genera un mapa de calor para la matriz de covarianza"""
    # Cálculo de la matriz de covarianza
    cov = df[columns].cov()
    
    fig = px.imshow(
        cov,
        text_auto='.4f',
        color_continuous_scale=[[0, "#FBEEE6"], [0.5, "#E69D6C"], [1, "#B37D59"]], 
        aspect="auto",
    )
    
    fig.update_layout(
        title="Matriz de Covarianza",
        # Ajuste de márgenes para que los nombres de variables largos no se corten
        margin=dict(l=50, r=50, t=50, b=50)
    )
    return fig

def make_distribution_figure(df, column, plot_kind):
    series = df[column].dropna()
    fig = go.Figure()

    if plot_kind in {"hist", "hist_density"}:
        histnorm_val = "probability density" if plot_kind == "hist_density" else None
        fig.add_trace(go.Histogram(
            x=series, 
            histnorm=histnorm_val,
            nbinsx=min(30, max(10, int(np.sqrt(len(series))))), 
            name="Histograma", 
            marker_color="#00e5a0", 
            opacity=0.8
        ))
        if plot_kind == "hist_density":
            try:
                kde = gaussian_kde(series)
                x_vals = np.linspace(series.min(), series.max(), 200)
                y_vals = kde(x_vals)
                
                fig.add_trace(go.Scatter(
                    x=x_vals, 
                    y=y_vals, 
                    mode='lines', 
                    name="Densidad KDE", 
                    line=dict(color="#7c8cf8", width=3)
                ))
            except Exception:
                pass
    elif plot_kind == "box":
        fig.add_trace(go.Box(x=series, name=column, marker_color="#ff6b6b", boxmean=True, orientation="h", boxpoints='outliers', jitter=0.3))
    fig.update_layout(title=f"{column} - {plot_kind.replace('_', ' ').title()}")
    return fig

def make_numeric_distribution_figure(df, column):
    """Create histogram with boxplot marginal for numeric distribution"""
    series = df[column].dropna()
    fig = px.histogram(
        df,
        x=column,
        nbins=50,
        title=f"{column} - Distribución",
        opacity=0.75,
        marginal='box'
    )
    return fig


def make_categorical_distribution_figure(df, column):
    """Create pie chart for categorical distribution"""
    series = df[column].dropna()

    # 1. ESCUDO PARA FECHAS: Verificar si el tipo de dato es datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        fig = go.Figure()
        fig.add_annotation(
            text="Visualización omitida: Tipo de dato Fecha/Tiempo.", 
            showarrow=False,
            font=dict(size=14, color="gray")
        )
        fig.update_layout(xaxis_visible=False, yaxis_visible=False)
        return fig
    
    value_counts = series.value_counts()

    # 2. ESCUDO DE CARDINALIDAD: Evitar colapso si hay más de 15 categorías distintas
    if len(value_counts) > 15:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Alta cardinalidad detectada ({len(value_counts)} valores únicos).<br>Gráfico circular omitido por rendimiento.", 
            showarrow=False,
            font=dict(size=14, color="orange")
        )
        fig.update_layout(xaxis_visible=False, yaxis_visible=False)
        return fig
    
    if len(value_counts) < 2:
        fig = go.Figure()
        fig.add_annotation(text="Se requieren al menos 2 valores únicos", showarrow=False)
        return fig
    
    fig = px.pie(
        values=value_counts.values,
        names=value_counts.index,
        title=f"{column} - Distribución"
    )
    return fig


def shapiro_wilk_table_html(df, columns):
    """Generate HTML table with Shapiro-Wilk normality test results"""
    rows = []
    
    for col in columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue

        series = df[col].dropna()
        
        # Skip if less than 3 samples (Shapiro-Wilk requires n >= 3)
        if len(series) < 3:
            continue

        # Límite matemático de Shapiro-Wilk (N <= 5000)
        # La librería scipy.stats advierte que para N > 5000 el p-value pierde precisión, por eso se toma una muestra representativa.
        if len(series) > 5000:
            series = series.sample(n=5000, random_state=42)

        # Manejo de excepciones por datos constantes
        try:
            w, p_value = shapiro(series)
        except Exception:
            # Si todos los valores son idénticos, shapiro puede fallar
            continue
                
        # Categorize closeness to 1
        if w >= 0.99:
            cercania = "Bastante"
        elif w >= 0.95:
            cercania = "Mucha"
        elif w >= 0.90:
            cercania = "Parecida"
        else:
            cercania = "No normal"
        
        # Categorize normality
        normal = "Sí" if p_value > 0.05 else "No"
        
        rows.append(f"<tr><td>{escape(str(col))}</td><td>{w:.4f}</td><td>{cercania}</td><td>{p_value:.4f}</td><td>{normal}</td></tr>")
    
    legend = """
    <div style="margin-top: 16px; color: var(--muted); font-size: 12px; line-height: 1.6;">
      <strong>Leyenda:</strong><br>
      <strong>W:</strong> Estadístico de Shapiro-Wilk (rango 0-1, cercano a 1 indica normalidad)<br>
      <strong>Cercania(W):</strong> Bastante (≥0.99) | Mucha (≥0.95) | Parecida (≥0.90) | No normal (<0.90)<br>
      <strong>P-value:</strong> Resultado del test. Si p > 0.05 → distribución normal, p ≤ 0.05 → no normal
    </div>
    """
    
    return f"""
    <div class="df-table-wrap">
      <table class="df-table">
        <thead><tr><th>var</th><th>w</th><th>cercania(w)</th><th>p-value</th><th>Normal (p-value)</th></tr></thead>
        <tbody>{''.join(rows) if rows else '<tr><td colspan="5">Sin columnas numéricas con suficientes datos</td></tr>'}</tbody>
      </table>
    </div>
    {legend}
    """

def make_scatter_plot_figure(df, col_x, col_y, col_color=None):
    """Create a scatter plot for bivariate analysis"""
    # Eliminar nulos solo de estas dos columnas para no graficar vacíos
    subset_cols = [col_x, col_y]
    if col_color:
        subset_cols.append(col_color)
        
    plot_df = df.dropna(subset=subset_cols)
    #plot_df = df.dropna(subset=[col_x, col_y])
    
    if plot_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No hay datos válidos para cruzar estas variables", showarrow=False)
        fig.update_layout(xaxis_visible=False, yaxis_visible=False)
        return fig

    # opacity=0.5 ayuda a ver la densidad cuando hay cientos de puntos solapados
    fig = px.scatter(
        plot_df, 
        x=col_x, 
        y=col_y,
        color=col_color,
        title=f"Dispersión: {col_x} vs {col_y}",
        opacity=0.6,
        marginal_x="histogram",
        marginal_y="histogram",
        color_discrete_sequence=["#7c8cf8"] if not col_color else px.colors.qualitative.Pastel 
    )
    return fig