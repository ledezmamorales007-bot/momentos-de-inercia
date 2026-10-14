from pathlib import Path
import zipfile

out = Path("/mnt/data/momentos_inercia_streamlit")
out.mkdir(parents=True, exist_ok=True)

app_code = r'''import math
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Momentos de inercia", layout="wide")
st.title("Calculadora de áreas compuestas y momentos de inercia")
st.write(
    "Introduce las figuras que forman la sección. Usa signo positivo para material "
    "añadido y negativo para huecos. La imagen es una referencia visual: sus medidas "
    "no se reconocen automáticamente."
)

def properties(row):
    kind = row["Tipo"]
    b = max(0.0, float(row["Base"]))
    h = max(0.0, float(row["Altura"]))
    r = max(0.0, float(row["Radio"]))
    x0, y0 = float(row["X anclaje"]), float(row["Y anclaje"])

    # Devuelve área y momentos centroidales propios:
    # Ix = integral(y^2 dA), Iy = integral(x^2 dA),
    # Ixy = integral(x*y dA).
    if kind == "Rectángulo":
        A = b*h
        dx, dy = b/2, h/2
        Ixc, Iyc, Ixyc = b*h**3/12, h*b**3/12, 0.0
    elif kind == "Cuadrado":
        h = b
        A = b*h
        dx, dy = b/2, h/2
        Ixc, Iyc, Ixyc = b*h**3/12, h*b**3/12, 0.0
    elif kind == "Triángulo rectángulo":
        # Vértices: (x0,y0), (x0+b,y0), (x0,y0+h).
        A = b*h/2
        dx, dy = b/3, h/3
        Ixc, Iyc = b*h**3/36, h*b**3/36
        Ixyc = -(b**2*h**2)/72
    elif kind == "Círculo":
        # X/Y anclaje: esquina inferior izquierda del cuadrado envolvente.
        A = math.pi*r**2
        dx = dy = r
        Ixc = Iyc = math.pi*r**4/4
        Ixyc = 0.0
    elif kind == "Semicírculo":
        # Semicírculo por encima de un diámetro horizontal; anclaje en extremo izquierdo.
        A = math.pi*r**2/2
        dx, dy = r, 4*r/(3*math.pi)
        Ixc = math.pi*r**4/8 - A*dy**2
        Iyc = math.pi*r**4/8
        Ixyc = 0.0
    elif kind == "Cuarto de círculo":
        # Cuarto de círculo hacia arriba y a la derecha desde el anclaje.
        A = math.pi*r**2/4
        dx = dy = 4*r/(3*math.pi)
        I_corner = math.pi*r**4/16
        Ixy_corner = r**4/8
        Ixc = I_corner - A*dy**2
        Iyc = I_corner - A*dx**2
        Ixyc = Ixy_corner - A*dx*dy
    else:
        raise ValueError("Tipo de figura no reconocido.")

    return {
        "A": A, "cx": x0+dx, "cy": y0+dy,
        "Ix_c": Ixc, "Iy_c": Iyc, "Ixy_c": Ixyc,
        "b": b, "h": h, "r": r
    }

def rotate_inertias(Ix, Iy, Ixy, degrees):
    """Transforma Ix, Iy e Ixy a ejes girados antihorariamente."""
    t = math.radians(degrees)
    c, s = math.cos(t), math.sin(t)
    Ix_new = c*c*Ix + s*s*Iy - 2*s*c*Ixy
    Iy_new = s*s*Ix + c*c*Iy + 2*s*c*Ixy
    Ixy_new = s*c*(Iy-Ix) + (c*c-s*s)*Ixy
    return Ix_new, Iy_new, Ixy_new

with st.sidebar:
    st.header("Imagen de referencia")
    image_file = st.file_uploader("Subir imagen PNG o JPG", type=["png", "jpg", "jpeg"])
    if image_file:
        st.image(image_file, caption="Referencia visual", use_container_width=True)

    st.header("Sistema de coordenadas")
    ox = st.number_input("X del nuevo origen", value=0.0, step=0.5, format="%.4f")
    oy = st.number_input("Y del nuevo origen", value=0.0, step=0.5, format="%.4f")
    angle = st.number_input("Giro de los ejes (grados antihorarios)", value=0.0, step=5.0, format="%.3f")
    unit = st.selectbox("Unidad de longitud", ["m", "cm", "mm", "in"], index=1)

st.subheader("1. Figuras de la sección")
st.markdown("""
**Signo:** `1` suma material; `-1` resta un hueco.

**Posición de anclaje:** para rectángulos, cuadrados y triángulos es la esquina inferior izquierda.
El triángulo rectángulo tiene vértices `(X, Y)`, `(X + base, Y)` y `(X, Y + altura)`.
Para círculos, el anclaje es la esquina inferior izquierda del cuadro que lo contiene.
Para semicírculos, es el extremo izquierdo del diámetro horizontal y la parte curva queda arriba.
Para cuartos de círculo, es la esquina del ángulo recto y el área queda arriba y a la derecha.
""")

default_data = pd.DataFrame([
    {"Tipo":"Rectángulo", "Signo":1, "Base":10.0, "Altura":5.0, "Radio":1.0, "X anclaje":0.0, "Y anclaje":0.0},
    {"Tipo":"Rectángulo", "Signo":-1, "Base":2.0, "Altura":2.0, "Radio":1.0, "X anclaje":4.0, "Y anclaje":1.5},
])
if "geometry_table" not in st.session_state:
    st.session_state.geometry_table = default_data.copy()

edited = st.data_editor(
    st.session_state.geometry_table,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="geometry_editor",
    column_config={
        "Tipo": st.column_config.SelectboxColumn(
            "Tipo", options=["Rectángulo","Cuadrado","Triángulo rectángulo","Círculo","Semicírculo","Cuarto de círculo"], required=True
        ),
        "Signo": st.column_config.SelectboxColumn("Signo", options=[1,-1], required=True),
        "Base": st.column_config.NumberColumn("Base", min_value=0.0, step=0.5, format="%.4f"),
        "Altura": st.column_config.NumberColumn("Altura", min_value=0.0, step=0.5, format="%.4f"),
        "Radio": st.column_config.NumberColumn("Radio", min_value=0.0, step=0.5, format="%.4f"),
        "X anclaje": st.column_config.NumberColumn("X anclaje", step=0.5, format="%.4f"),
        "Y anclaje": st.column_config.NumberColumn("Y anclaje", step=0.5, format="%.4f"),
    },
)
st.session_state.geometry_table = edited.copy()

left, right = st.columns(2)
with left:
    if st.button("Añadir fila rectangular"):
        row = pd.DataFrame([{"Tipo":"Rectángulo","Signo":1,"Base":1.0,"Altura":1.0,"Radio":1.0,"X anclaje":0.0,"Y anclaje":0.0}])
        st.session_state.geometry_table = pd.concat([edited, row], ignore_index=True)
        st.rerun()
with right:
    if st.button("Restablecer ejemplo"):
        st.session_state.geometry_table = default_data.copy()
        st.rerun()

records, errors = [], []
for i, row in edited.iterrows():
    try:
        p = properties(row)
        sign = int(row["Signo"])
        if sign not in (-1, 1):
            raise ValueError("El signo debe ser 1 o -1.")
        if p["A"] <= 0:
            errors.append(f"Fila {i+1}: área cero. Comprueba la base, altura o radio.")
            continue

        # Coordenadas del centroide elemental en los ejes configurados.
        theta = math.radians(angle)
        dx, dy = p["cx"]-ox, p["cy"]-oy
        xp = math.cos(theta)*dx + math.sin(theta)*dy
        yp = -math.sin(theta)*dx + math.cos(theta)*dy

        Ixc, Iyc, Ixyc = rotate_inertias(p["Ix_c"], p["Iy_c"], p["Ixy_c"], angle)
        A_signed = sign*p["A"]
        Ix_o = sign*(Ixc + p["A"]*yp**2)
        Iy_o = sign*(Iyc + p["A"]*xp**2)
        Ixy_o = sign*(Ixyc + p["A"]*xp*yp)

        records.append({
            "N.º":i+1, "Tipo":row["Tipo"], "Signo":"+" if sign==1 else "−",
            "Base":p["b"], "Altura":p["h"], "Radio":p["r"],
            "Área geométrica":p["A"], "Área con signo":A_signed,
            "X centroide":xp, "Y centroide":yp,
            "A·X":A_signed*xp, "A·Y":A_signed*yp,
            "Ix propio centroidal (con signo)":sign*Ixc,
            "Iy propio centroidal (con signo)":sign*Iyc,
            "Ix respecto al origen":Ix_o, "Iy respecto al origen":Iy_o,
            "Ixy respecto al origen":Ixy_o,
            "_A":A_signed, "_x":xp, "_y":yp, "_Ix":Ix_o, "_Iy":Iy_o, "_Ixy":Ixy_o
        })
    except Exception as exc:
        errors.append(f"Fila {i+1}: {exc}")

for error in errors:
    st.warning(error)

if not records:
    st.error("Añade al menos una figura con dimensiones positivas.")
    st.stop()

df = pd.DataFrame(records)
At = float(df["_A"].sum())
if abs(At) < 1e-12:
    st.error("El área total con signo es cero. No se puede calcular el centroide. Revisa los signos y dimensiones.")
    st.stop()

xbar = float((df["_A"]*df["_x"]).sum()/At)
ybar = float((df["_A"]*df["_y"]).sum()/At)
Ix_o, Iy_o, Ixy_o = float(df["_Ix"].sum()), float(df["_Iy"].sum()), float(df["_Ixy"].sum())
Ix_c = Ix_o - At*ybar**2
Iy_c = Iy_o - At*xbar**2
Ixy_c = Ixy_o - At*xbar*ybar

# Los autovalores de esta matriz son los momentos principales del área.
inertia_matrix = np.array([[Iy_c, -Ixy_c], [-Ixy_c, Ix_c]], dtype=float)
values, vectors = np.linalg.eigh(inertia_matrix)
Imin, Imax = float(values[0]), float(values[1])
vmax = vectors[:, 1]
principal_angle = (math.degrees(math.atan2(float(vmax[1]), float(vmax[0])))+90) % 180 - 90

st.subheader("2. Tabla de cálculo")
columns = [
    "N.º","Tipo","Signo","Base","Altura","Radio","Área geométrica","Área con signo",
    "X centroide","Y centroide","A·X","A·Y",
    "Ix propio centroidal (con signo)","Iy propio centroidal (con signo)",
    "Ix respecto al origen","Iy respecto al origen","Ixy respecto al origen"
]
st.dataframe(df[columns].round(6), use_container_width=True, hide_index=True)

st.markdown("**Sumatorias**")
sum_values = {
    "Σ área geométrica":float(df["Área geométrica"].sum()),
    "Σ área con signo":At,
    "Σ(A·X)":float((df["_A"]*df["_x"]).sum()),
    "Σ(A·Y)":float((df["_A"]*df["_y"]).sum()),
    "Σ Ix respecto al origen":Ix_o,
    "Σ Iy respecto al origen":Iy_o,
    "Σ Ixy respecto al origen":Ixy_o,
}
st.dataframe(pd.DataFrame([sum_values], index=["Total"]).round(6), use_container_width=True)

st.subheader("3. Resultados")
a,b,c = st.columns(3)
a.metric("Área total con signo", f"{At:.6f} {unit}²")
b.metric("Centroide X", f"{xbar:.6f} {unit}")
c.metric("Centroide Y", f"{ybar:.6f} {unit}")
a,b,c = st.columns(3)
a.metric("Ix centroidal", f"{Ix_c:.6f} {unit}⁴")
b.metric("Iy centroidal", f"{Iy_c:.6f} {unit}⁴")
c.metric("Ixy centroidal", f"{Ixy_c:.6f} {unit}⁴")
a,b,c = st.columns(3)
a.metric("Momento principal máximo", f"{Imax:.6f} {unit}⁴")
b.metric("Momento principal mínimo", f"{Imin:.6f} {unit}⁴")
c.metric("Ángulo del eje principal máximo", f"{principal_angle:.6f}°")

with st.expander("4. Procedimiento y fórmulas"):
    st.markdown("### Centroide compuesto")
    st.latex(r"A_T=\sum_i s_i A_i")
    st.latex(r"\bar{x}=\frac{\sum_i s_i A_i x_i}{A_T},\qquad \bar{y}=\frac{\sum_i s_i A_i y_i}{A_T}")
    st.write(f"Σ(A·X) = {float((df['_A']*df['_x']).sum()):.8f} {unit}³")
    st.write(f"Σ(A·Y) = {float((df['_A']*df['_y']).sum()):.8f} {unit}³")
    st.write(f"X̄ = {xbar:.8f} {unit}; Ȳ = {ybar:.8f} {unit}")
    st.markdown("### Steiner: del centroide de cada parte al origen elegido")
    st.latex(r"I_{x,O}=\sum_i s_i\left(I_{x,c_i}+A_i y_i'^2\right)")
    st.latex(r"I_{y,O}=\sum_i s_i\left(I_{y,c_i}+A_i x_i'^2\right)")
    st.latex(r"I_{xy,O}=\sum_i s_i\left(I_{xy,c_i}+A_i x_i'y_i'\right)")
    st.write(f"Ix,O = {Ix_o:.8f} {unit}⁴")
    st.write(f"Iy,O = {Iy_o:.8f} {unit}⁴")
    st.write(f"Ixy,O = {Ixy_o:.8f} {unit}⁴")
    st.markdown("### Traslado al centroide de la sección")
    st.latex(r"I_{\bar{x}}=I_{x,O}-A_T\bar{y}^{\,2}")
    st.latex(r"I_{\bar{y}}=I_{y,O}-A_T\bar{x}^{\,2}")
    st.latex(r"I_{\bar{x}\bar{y}}=I_{xy,O}-A_T\bar{x}\bar{y}")
    st.write(f"Ix centroidal = {Ix_c:.8f} {unit}⁴")
    st.write(f"Iy centroidal = {Iy_c:.8f} {unit}⁴")
    st.write(f"Ixy centroidal = {Ixy_c:.8f} {unit}⁴")
    st.markdown("### Momentos principales")
    st.latex(r"I_{1,2}=\frac{I_{\bar{x}}+I_{\bar{y}}}{2}\pm\sqrt{\left(\frac{I_{\bar{x}}-I_{\bar{y}}}{2}\right)^2+I_{\bar{x}\bar{y}}^2}")
    st.write(f"I máximo = {Imax:.8f} {unit}⁴")
    st.write(f"I mínimo = {Imin:.8f} {unit}⁴")
    st.write(f"Ángulo calculado para el eje asociado al momento máximo = {principal_angle:.8f}°.")

with st.expander("5. Comprobaciones automáticas"):
    checks = [
        ("Área total distinta de cero", abs(At)>1e-12),
        ("Ix centroidal no negativo (tolerancia numérica)", Ix_c>=-1e-8),
        ("Iy centroidal no negativo (tolerancia numérica)", Iy_c>=-1e-8),
        ("I máximo mayor o igual que I mínimo", Imax>=Imin-1e-9),
        ("Suma de momentos principales = Ix + Iy", abs((Imax+Imin)-(Ix_c+Iy_c)) <= 1e-6*max(1.0,abs(Imax+Iy_c))),
    ]
    for label, ok in checks:
        st.write(("✅ " if ok else "⚠️ ") + label)
    st.caption("Estas comprobaciones ayudan a detectar errores, pero no sustituyen la revisión de la geometría introducida.")

st.subheader("6. Descargar tabla")
csv_data = df[columns].to_csv(index=False).encode("utf-8-sig")
st.download_button("Descargar tabla CSV", data=csv_data, file_name="tabla_momentos_inercia.csv", mime="text/csv")

st.warning(
    "Comprueba que todas las dimensiones usen la misma unidad. Esta versión admite figuras elementales "
    "alineadas con los ejes originales; el giro corresponde al sistema de coordenadas, no a la rotación "
    "individual de cada figura. La fotografía no se interpreta automáticamente."
)
'''

requirements = """streamlit>=1.35
pandas>=2.0
numpy>=1.24
"""

readme = """# Calculadora de momentos de inercia de áreas compuestas

Aplicación en Streamlit para introducir figuras elementales, sumar material, restar huecos y calcular centroide y momentos de inercia.

## Archivos
- `app.py`: aplicación.
- `requirements.txt`: dependencias.
- `README.md`: instrucciones.

## Ejecutar en el ordenador
1. Instala Python.
2. Abre una terminal en la carpeta de estos archivos.
3. Ejecuta:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar en GitHub y Streamlit Community Cloud
1. Sube `app.py`, `requirements.txt` y `README.md` a un repositorio de GitHub.
2. Entra en https://share.streamlit.io/
3. Conecta tu cuenta de GitHub y crea una app nueva.
4. Selecciona el repositorio, la rama y `app.py` como archivo principal.

## Alcance de esta versión
- Rectángulos, cuadrados, triángulos rectángulos, círculos, semicírculos y cuartos de círculo.
- Signos positivos para material añadido y negativos para huecos.
- Tabla editable con dimensiones y posiciones.
- Origen de coordenadas y giro de ejes configurables.
- Centroide, inercias respecto al origen, inercias centroidales y momentos principales.
- Imagen PNG/JPG como referencia visual; no reconoce automáticamente la geometría de la imagen.

## Nota técnica
Verifica la geometría, las dimensiones, la orientación de los triángulos y el signo de los huecos antes de usar los resultados en un informe o diseño.
"""

(out / "app.py").write_text(app_code, encoding="utf-8")
(out / "requirements.txt").write_text(requirements, encoding="utf-8")
(out / "README.md").write_text(readme, encoding="utf-8")

zip_path = Path("/mnt/data/momentos_inercia_streamlit.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for name in ["app.py", "requirements.txt", "README.md"]:
        z.write(out / name, arcname=name)

print("Archivos creados correctamente:")
print(f"- {out / 'app.py'}")
print(f"- {out / 'requirements.txt'}")
print(f"- {out / 'README.md'}")
print(f"- {zip_path}")
