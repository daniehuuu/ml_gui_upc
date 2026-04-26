# Informe
## Antecedentes y Problemática del Problema
### Contexto Global

El aprendizaje de Machine Learning y Data Science ha crecido aceleradamente en universidades, bootcamps y programas corporativos debido a la alta demanda de perfiles analíticos. Sin embargo, a nivel mundial persiste una dificultad común: la enseñanza suele centrarse en teoría matemática y desarrollo manual en notebooks, especialmente en Jupyter Notebook, dejando en segundo plano herramientas integradas que faciliten la comprensión visual del flujo completo de un proyecto de ML.

En entornos profesionales sí se utilizan plataformas más ágiles como Google Cloud Vertex AI, Microsoft Azure ML o Amazon Web Services SageMaker, donde se automatizan tareas de exploración de datos, entrenamiento y monitoreo. Esto evidencia una diferencia entre formación académica tradicional y práctica empresarial moderna.

### Contexto Local

En universidades peruanas, especialmente en carreras de ingeniería y computación, los cursos de Machine Learning suelen incluir teoría, algoritmos supervisados/no supervisados y desarrollo en Python mediante notebooks. En el caso del curso de Machine Learning de la UPC, se busca que el estudiante implemente proyectos completos considerando preprocesamiento, modelos y conclusiones relevantes .

No obstante, aunque el curso contempla talleres y desarrollo práctico, no se menciona una plataforma propia orientada a visualización automática, diagnóstico de datos o experimentación simplificada. Esto obliga a que muchos alumnos repitan procesos manuales en cada práctica: revisión de nulos, tratamiento de outliers, codificación, selección de variables y comparación de modelos.

### Soluciones Existentes

Actualmente existen alternativas parciales:

- Jupyter Notebook: flexible, pero requiere programación manual.
- Google Colab: colaborativo, pero sigue siendo code-first.
- Power BI: excelente para dashboards, limitado para ML end-to-end.
- RapidMiner: potente pero menos usada en entorno universitario local.
- Orange Data Mining: amigable, pero no siempre integrada al currículo.
- KNIME: robusta, aunque más orientada a negocio.

### Brecha 

Existe una oportunidad clara para desarrollar una herramienta académica híbrida que combine:

- Visualización automática.
- Preprocesamiento guiado.
- Comparación de modelos ML.
- Exportación de código Python.
- Dashboard educativo.
- Escalabilidad hacia necesidades empresariales.

Es decir, una plataforma pensada para estudiantes que aprenden, pero suficientemente sólida para proyectos reales.

### 5Ws y 2Hs
**Who (¿Quiénes se ven afectados?)**  

- Estudiantes de Machine Learning
- Docentes que desean acelerar prácticas
- Universidades que buscan innovación educativa
- Futuros profesionales de datos

**What (¿Qué ocurre?)**

Los estudiantes de Machine Learning reciben teoría y programación en notebooks, pero no cuentan con una plataforma visual e integral para experimentar, analizar datos y comprender rápidamente el flujo completo de un proyecto de ML.

**Where (¿Dónde ocurre?)** 

En universidades y centros educativos donde se enseña ML principalmente mediante notebooks y clases teóricas. Localmente, en cursos universitarios como el de la UPC.

**When (¿Cuándo ocurre?)** 

Durante laboratorios, tareas, proyectos y etapas iniciales de aprendizaje donde el alumno necesita explorar datasets, limpiar datos y probar modelos rápidamente.

**Why (¿Por qué ocurre?)**

Porque la enseñanza tradicional prioriza fundamentos matemáticos y codificación manual, mientras que las herramientas modernas de automatización y visualización no suelen integrarse formalmente al curso.

**How (¿Cómo se manifiesta?)** 

El alumno dedica tiempo excesivo a programar tareas básicas como limpieza, gráficos, imputación o evaluación en lugar de concentrarse en interpretar resultados y tomar decisiones analíticas.

**How much (¿Cuánto impacta?)** 

Impacta en horas de trabajo perdidas por práctica, menor rendimiento académico, menor velocidad de prototipado y preparación limitada para entornos laborales reales.

## Lean UX Problem Statement

**Hemos observado** que los estudiantes de cursos de Machine Learning reciben formación teórica y desarrollan prácticas principalmente en notebooks y código manual, sin contar con una plataforma visual e integrada para experimentar con algoritmos, preprocesamiento y evaluación de modelos, **lo cual está causando** mayor tiempo invertido en tareas operativas, dificultad para comprender el flujo completo de ML y menor conexión con herramientas usadas en entornos profesionales.

**¿Cómo podemos** diseñar una plataforma educativa interactiva de Machine Learning **para que** los estudiantes universitarios **logren** aprender de forma más práctica, rápida y aplicada mediante experimentación guiada, visualización de resultados y comparación sencilla de modelos?

## Lean UX Assumptions

**Usuario**

Creemos que nuestros usuarios son estudiantes universitarios de carreras de computación, ingeniería o afines que están llevando cursos de Machine Learning y actualmente aprenden mediante clases teóricas, notebooks y código manual para ejecutar prácticas.

**Problema**

Creemos que el principal obstáculo es la ausencia de una herramienta académica intuitiva que simplifique el flujo completo de Machine Learning (carga de datos, limpieza, entrenamiento, evaluación y visualización), obligando al estudiante a enfocarse más en programar procesos repetitivos que en comprender conceptos.

**Comportamiento**

Creemos que si ofrecemos una plataforma visual con flujos guiados, comparación de modelos y exportación de código Python, el estudiante experimentará más veces con datasets reales, entenderá mejor los resultados y mejorará su desempeño académico.

**Riesgo 1**

No sabemos si los estudiantes realmente cambiarán su forma actual de trabajo basada en notebooks y adoptarán una nueva plataforma.

**Riesgo 2**

No sabemos si los estudiantes valorarán más la facilidad de uso que la flexibilidad total que ofrece programar manualmente en Python.

**Riesgo 3**

No sabemos si una interfaz visual mejorará realmente la comprensión conceptual o solo acelerará tareas mecánicas.

**Riesgo 4**

No sabemos si los docentes estarán dispuestos a integrar la plataforma dentro de sus cursos y evaluaciones.

**Riesgo 5**

No sabemos si la plataforma podrá cubrir suficientes algoritmos, técnicas de preprocesamiento y métricas como para ser útil académicamente.

**Riesgo 6**

No sabemos si los estudiantes confiarán en resultados automáticos sin entender el código o la lógica detrás del proceso.

**Riesgo 7**

No sabemos si la exportación de código Python será percibida como una ventaja real o será poco utilizada.

**Riesgo 8**

No sabemos si universidades locales invertirán tiempo o recursos en implementar una solución de este tipo.

## Competitors

| Competidor | Tipo | Enfoque Principal | Funciones Relacionadas al Curso (según sílabo) | Ventajas | Limitaciones frente a nuestra propuesta |
|---|---|---|---|---|---|
| Orange Data Mining | Open source desktop | Machine Learning visual por bloques | Clasificación, regresión, clustering, feature selection, métricas | Interfaz amigable, ideal para aprender conceptos | Menor adopción local, limitado para proyectos escalables |
| KNIME Analytics Platform | Open source / empresarial | Pipelines visuales de analítica | ETL, preprocesamiento, clasificación, regresión, clustering, dashboards | Muy robusto, flujo visual profesional | Complejo para principiantes |
| RapidMiner | Comercial / educativo | AutoML + flujos visuales | Limpieza, modelado, comparación de algoritmos, métricas | Muy completo, orientado a negocio | Licencias limitadas, menos accesible para estudiantes |
| Weka | Open source académico | Suite clásica de ML | Árboles, Bayes, KNN, clustering, validación cruzada | Muy alineado a cursos universitarios | Interfaz antigua, experiencia menos moderna |
| Dataiku DSS | Empresarial | Data Science colaborativo | Preparación de datos, AutoML, dashboards, despliegue | Excelente para industria real | Costoso y complejo para entorno académico |
| H2O.ai / Driverless AI | Empresarial / AutoML | Automatización de modelos | Clasificación, regresión, feature engineering, explainability | Muy potente para benchmarking | Menos enfoque didáctico |
| PyCaret | Librería open source | Low-code ML en Python | Comparación de modelos, métricas, tuning, clasificación/regresión | Ideal para acelerar prácticas | Requiere código, no interfaz visual nativa |
| Streamlit ML Dashboards (GitHub) | Repositorios reales open source | Dashboards hechos en Python | EDA, predicción, comparación de modelos, despliegue | Muy cercano a lo que pide el curso (dashboard + ML) | Cada repo depende del autor, no estándar educativo |
| Auto-sklearn | Open source | AutoML sobre scikit-learn | Selección automática de modelos, tuning | Excelente para comparar algoritmos | No enfocado en enseñanza visual |
| MLJAR / AutoML | Plataforma / OSS | AutoML simple | Clasificación, regresión, leaderboard | Fácil uso | Menos profundidad pedagógica |
