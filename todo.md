 # Overview
  - [x] Añadir el dtype de ndatetime64[ns]
 
 # EDA
 - [x] Estadísticas descriptivas para variables numéricas y categóricas (df.describe())
 - [x] Visualización de distribuciones (histogramas)
 - [x] Identificación de correlaciones
 - [] Veo que eda_dist_plot es capaz de graficar un histograma con su gráfica de densidad KDE. Me gustaría que se implemente esa gráfica KDE en eda_numeric_stats tambié. Entonces a eda_numeric_stats se le añadiría (dentro del mismo histograma) el gráfica KDE. No elimines el marginal = box.
 - [] Importar dataset desde kaggle
 - [] Add individual select-bound-output and code for input
 - [] Scatter matrix with plotly. 

 ```py
# This was not working
selected = input.eda_num_cols() or get_num_cols(df)
selected = [col for col in selected if col in df.columns]
```