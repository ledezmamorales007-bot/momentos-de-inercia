# Calculadora de Momentos Principales de Inercia

## Descripción
Aplicación desarrollada en Python para calcular las propiedades geométricas de áreas planas y determinar sus momentos principales de inercia. Está orientada al aprendizaje de Resistencia de Materiales e Ingeniería Civil.

## Funcionalidades
- Cálculo del área y centroide de una sección.
- Cálculo de los momentos de inercia respecto a los ejes centroidales: Ix e Iy.
- Cálculo del producto de inercia Ixy.
- Determinación de los momentos principales máximo y mínimo.
- Cálculo del ángulo de orientación de los ejes principales.
- Análisis de secciones compuestas y huecos.
- Ingreso de polígonos irregulares mediante coordenadas.
- Representación gráfica de la sección y sus ejes principales.
- Exportación de resultados en formato CSV.

## Tecnologías utilizadas
- Python
- Streamlit
- NumPy
- Pandas
- Matplotlib

## Ejecución
La aplicación puede publicarse como una aplicación web mediante Streamlit Community Cloud.

1. Subir los archivos `app.py` y `requirements.txt` al repositorio de GitHub.
2. Entrar en https://share.streamlit.io/
3. Conectar la cuenta de GitHub.
4. Crear una aplicación nueva y seleccionar el repositorio.
5. Elegir `app.py` como archivo principal.
6. Publicar la aplicación y abrir el enlace generado.

## Unidades
Las dimensiones deben ingresarse utilizando una misma unidad. Por ejemplo, si se utilizan centímetros, el área se expresa en cm² y los momentos de inercia en cm⁴.

## Nota
Esta aplicación tiene fines educativos. Los resultados deben verificarse con ejercicios resueltos manualmente antes de utilizarse en cálculos de ingeniería reales.
