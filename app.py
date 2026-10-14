import math
import re
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

st.set_page_config(page_title="Momentos principales de inercia", page_icon="📐", layout="wide")

st.title("Calculadora de momentos principales de inercia")
st.caption("Áreas planas · secciones compuestas · huecos · polígonos por coordenadas")

st.info(
    "Convención: Ix = ∫y² dA, Iy = ∫x² dA e Ixy = ∫xy dA. "
    "Las coordenadas y dimensiones deben utilizar una misma unidad (por ejemplo, cm). "
    "Los momentos resultan en esa unidad elevada a la cuarta potencia (por ejemplo, cm⁴)."
)

if "shapes" not in st.session_state:
    st.session_state.shapes = []

def parse_vertices(raw):
    """Lee una coordenada x,y por línea."""
    pts = []
    for line_no, line in enumerate(raw.strip().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        parts = re.split(r"[,;\s]+", line)
        if len(parts) != 2:
            raise ValueError(f"Línea {line_no}: escribe exactamente x,y.")
        try:
            x, y = float(parts[0]), float(parts[1])
        except ValueError:
            raise ValueError(f"Línea {line_no}: las coordenadas deben ser números.")
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError(f"Línea {line_no}: usa valores finitos.")
        pts.append((x, y))
    if len(pts) < 3:
        raise ValueError("Un polígono necesita al menos 3 vértices.")
    if len(set(pts)) < 3:
        raise ValueError("El polígono debe tener al menos 3 puntos distintos.")
    return pts

def transform_points(points, tx, ty, angle_deg):
    """Rota cada punto alrededor del origen local y luego lo traslada."""
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return [(tx + x*c - y*s, ty + x*s + y*c) for x, y in points]

def polygon_properties(points):
    """Propiedades geométricas exactas de un polígono simple; devuelve área positiva."""
    n = len(points)
    cross_sum = 0.0
    cx_num = cy_num = ix0_num = iy0_num = ixy0_num = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        cr = x1*y2 - x2*y1
        cross_sum += cr
        cx_num += (x1 + x2) * cr
        cy_num += (y1 + y2) * cr
        ix0_num += (y1*y1 + y1*y2 + y2*y2) * cr
        iy0_num += (x1*x1 + x1*x2 + x2*x2) * cr
        ixy0_num += (2*x1*y1 + x1*y2 + x2*y1 + 2*x2*y2) * cr

    signed_area = cross_sum / 2.0
    if abs(signed_area) < 1e-12:
        raise ValueError("El polígono tiene área nula o casi nula.")
    orientation = 1.0 if signed_area > 0 else -1.0
    area = abs(signed_area)
    cx = cx_num / (6.0 * signed_area)
    cy = cy_num / (6.0 * signed_area)
    ix0 = orientation * ix0_num / 12.0
    iy0 = orientation * iy0_num / 12.0
    ixy0 = orientation * ixy0_num / 24.0
    ix = ix0 - area * cy**2
    iy = iy0 - area * cx**2
    ixy = ixy0 - area * cx * cy

    # Elimina pequeños residuos negativos debidos al redondeo numérico.
    tol = 1e-10 * max(1.0, abs(ix0), abs(iy0))
    if ix < 0 and abs(ix) < tol: ix = 0.0
    if iy < 0 and abs(iy) < tol: iy = 0.0
    return {"A": area, "cx": cx, "cy": cy, "Ix": ix, "Iy": iy, "Ixy": ixy}

def component_properties(shape):
    kind = shape["kind"]
    sign = -1.0 if shape.get("hole", False) else 1.0
    if kind == "Círculo":
        r = shape["r"]
        if r <= 0:
            raise ValueError("El radio debe ser mayor que cero.")
        A = math.pi * r*r
        I = math.pi * r**4 / 4.0
        return {
            "A": sign*A, "cx": shape["tx"], "cy": shape["ty"],
            "Ix": sign*I, "Iy": sign*I, "Ixy": 0.0,
            "plot_kind": "circle", "r": r, "points": None,
            "name": shape["name"], "hole": shape.get("hole", False)
        }

    if kind == "Rectángulo":
        w, h = shape["w"], shape["h"]
        if w <= 0 or h <= 0:
            raise ValueError("El ancho y la altura deben ser mayores que cero.")
        local = [(-w/2,-h/2), (w/2,-h/2), (w/2,h/2), (-w/2,h/2)]
    else:
        local = shape["vertices"]

    points = transform_points(local, shape["tx"], shape["ty"], shape.get("angle", 0.0))
    p = polygon_properties(points)
    return {
        "A": sign*p["A"], "cx": p["cx"], "cy": p["cy"],
        "Ix": sign*p["Ix"], "Iy": sign*p["Iy"], "Ixy": sign*p["Ixy"],
        "plot_kind": "polygon", "r": None, "points": points,
        "name": shape["name"], "hole": shape.get("hole", False)
    }

def calculate(shapes):
    if not shapes:
        raise ValueError("Agrega al menos una figura.")
    props = [component_properties(s) for s in shapes]
    A = sum(p["A"] for p in props)
    if A <= 1e-10:
        raise ValueError("El área neta debe ser positiva. Revisa las figuras y los huecos.")
    cx = sum(p["A"]*p["cx"] for p in props) / A
    cy = sum(p["A"]*p["cy"] for p in props) / A
    Ix = sum(p["Ix"] + p["A"]*(p["cy"]-cy)**2 for p in props)
    Iy = sum(p["Iy"] + p["A"]*(p["cx"]-cx)**2 for p in props)
    Ixy = sum(p["Ixy"] + p["A"]*(p["cx"]-cx)*(p["cy"]-cy) for p in props)

    avg = (Ix + Iy) / 2.0
    rad = math.sqrt(max(0.0, ((Ix-Iy)/2.0)**2 + Ixy**2))
    Imax, Imin = avg + rad, avg - rad
    theta = 0.5 * math.degrees(math.atan2(-2.0*Ixy, Ix-Iy))
    # Comprueba que los momentos no sean negativos por errores importantes.
    tol = 1e-9 * max(1.0, abs(Imax))
    if Imin < -tol:
        raise ValueError("Se obtuvo un momento principal negativo. Revisa la geometría o los huecos.")
    Imin = max(0.0, Imin)
    return props, {"A": A, "cx": cx, "cy": cy, "Ix": Ix, "Iy": Iy,
                   "Ixy": Ixy, "Imax": Imax, "Imin": Imin, "theta": theta}

def draw_section(props, result):
    fig, ax = plt.subplots(figsize=(8, 6))
    for p in props:
        if p["plot_kind"] == "circle":
            patch = Circle((p["cx"], p["cy"]), p["r"],
                           facecolor=("white" if p["hole"] else "#9ecae1"),
                           edgecolor=("crimson" if p["hole"] else "#1f4e79"),
                           linewidth=2, hatch="///" if p["hole"] else None)
            ax.add_patch(patch)
        else:
            pts = p["points"]
            xs = [q[0] for q in pts] + [pts[0][0]]
            ys = [q[1] for q in pts] + [pts[0][1]]
            ax.fill(xs, ys, facecolor=("white" if p["hole"] else "#9ecae1"),
                    edgecolor=("crimson" if p["hole"] else "#1f4e79"),
                    linewidth=2, hatch="///" if p["hole"] else None, alpha=0.85)
    cx, cy = result["cx"], result["cy"]
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    span = max(xmax-xmin, ymax-ymin, 1.0)
    # Ejes centroidales globales
    ax.axvline(cx, color="darkgreen", linestyle="--", linewidth=1.5, label="Eje centroidal vertical")
    ax.axhline(cy, color="darkorange", linestyle="--", linewidth=1.5, label="Eje centroidal horizontal")
    # Ejes principales que pasan por el centroide
    th = math.radians(result["theta"])
    L = span * 0.65
    t = np.array([-L, L])
    ax.plot(cx + t*math.cos(th), cy + t*math.sin(th), color="purple",
            linewidth=2, label=f"Eje principal Imax ({result['theta']:.2f}°)")
    ax.plot(cx - t*math.sin(th), cy + t*math.cos(th), color="teal",
            linewidth=2, label="Eje principal perpendicular")
    ax.scatter([cx], [cy], color="black", zorder=5)
    ax.annotate(f"G ({cx:.3g}, {cy:.3g})", (cx, cy), xytext=(6, 6),
                textcoords="offset points", fontsize=9)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Sección, centroide y ejes principales")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    return fig

with st.sidebar:
    st.header("Agregar una figura")
    kind = st.selectbox("Tipo de figura", ["Rectángulo", "Círculo", "Polígono / triángulo"])
    name = st.text_input("Nombre", value=f"Figura {len(st.session_state.shapes)+1}")
    hole = st.checkbox("Es un hueco (área negativa)")
    st.caption("Las posiciones x, y son las coordenadas del centro del rectángulo/círculo o del origen local del polígono.")
    tx = st.number_input("Posición x", value=0.0, step=1.0, format="%.6f")
    ty = st.number_input("Posición y", value=0.0, step=1.0, format="%.6f")
    angle = st.number_input("Rotación (grados, antihorario)", value=0.0, step=5.0, format="%.4f")

    if kind == "Rectángulo":
        w = st.number_input("Ancho", min_value=0.000001, value=10.0, step=1.0)
        h = st.number_input("Altura", min_value=0.000001, value=5.0, step=1.0)
        st.caption("El rectángulo se centra en (x, y) y luego se rota.")
    elif kind == "Círculo":
        r = st.number_input("Radio", min_value=0.000001, value=2.0, step=0.5)
        st.caption("Para un círculo, la rotación no cambia sus propiedades.")
    else:
        raw = st.text_area("Vértices locales (un x,y por línea)",
                           value="0,0\n4,0\n2,3", height=130,
                           help="El polígono se rota alrededor del origen local (0,0) y luego se traslada a (x,y).")
        st.caption("Triángulos y polígonos se introducen con sus vértices; no repitas el primer punto al final.")

    add = st.button("➕ Agregar figura", type="primary", use_container_width=True)
    if add:
        try:
            shape = {"kind": kind, "name": name.strip() or f"Figura {len(st.session_state.shapes)+1}",
                     "hole": hole, "tx": float(tx), "ty": float(ty), "angle": float(angle)}
            if kind == "Rectángulo":
                shape.update({"w": float(w), "h": float(h)})
            elif kind == "Círculo":
                shape.update({"r": float(r)})
            else:
                shape.update({"vertices": parse_vertices(raw)})
            # Validación geométrica inmediata
            component_properties(shape)
            st.session_state.shapes.append(shape)
            st.success("Figura agregada.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    if st.button("Cargar ejemplo: sección en L", use_container_width=True):
        st.session_state.shapes = [
            {"kind":"Rectángulo","name":"Ala horizontal","hole":False,"tx":5.0,"ty":1.0,"angle":0.0,"w":10.0,"h":2.0},
            {"kind":"Rectángulo","name":"Ala vertical","hole":False,"tx":1.0,"ty":5.0,"angle":0.0,"w":2.0,"h":8.0},
            {"kind":"Rectángulo","name":"Solape retirado","hole":True,"tx":1.0,"ty":1.0,"angle":0.0,"w":2.0,"h":2.0}
        ]
        st.rerun()
    if st.button("Borrar todas las figuras", use_container_width=True):
        st.session_state.shapes = []
        st.rerun()

st.subheader("1. Figuras de la sección")
if not st.session_state.shapes:
    st.write("Todavía no hay figuras. Agrega una desde el panel izquierdo o carga el ejemplo.")
else:
    rows = []
    for i, s in enumerate(st.session_state.shapes):
        if s["kind"] == "Rectángulo":
            dim = f"{s['w']:g} × {s['h']:g}"
        elif s["kind"] == "Círculo":
            dim = f"r = {s['r']:g}"
        else:
            dim = f"{len(s['vertices'])} vértices"
        rows.append({"N.º": i+1, "Nombre": s["name"], "Tipo": s["kind"],
                     "Dimensiones": dim, "Hueco": "Sí" if s["hole"] else "No",
                     "x": s["tx"], "y": s["ty"], "Rotación (°)": s.get("angle",0.0)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    choices = [f"{i+1}. {s['name']} ({s['kind']})" for i,s in enumerate(st.session_state.shapes)]
    to_remove = st.selectbox("Selecciona una figura para eliminar", choices, key="remove_choice")
    if st.button("Eliminar figura seleccionada"):
        idx = choices.index(to_remove)
        st.session_state.shapes.pop(idx)
        st.rerun()

st.subheader("2. Resultados")
if st.session_state.shapes:
    try:
        props, res = calculate(st.session_state.shapes)
        c1, c2, c3 = st.columns(3)
        c1.metric("Área neta", f"{res['A']:.6g}")
        c2.metric("Centroide x̄", f"{res['cx']:.6g}")
        c3.metric("Centroide ȳ", f"{res['cy']:.6g}")
        c4, c5, c6 = st.columns(3)
        c4.metric("Ix centroidal", f"{res['Ix']:.6g}")
        c5.metric("Iy centroidal", f"{res['Iy']:.6g}")
        c6.metric("Ixy centroidal", f"{res['Ixy']:.6g}")
        c7, c8, c9 = st.columns(3)
        c7.metric("I principal máximo", f"{res['Imax']:.6g}")
        c8.metric("I principal mínimo", f"{res['Imin']:.6g}")
        c9.metric("Ángulo del eje de Imax", f"{res['theta']:.4f}°")
        st.caption("Las unidades de Ix, Iy, Ixy, Imax e Imin son la cuarta potencia de la unidad usada para las dimensiones.")
        fig = draw_section(props, res)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        with st.expander("Ver propiedades por componente"):
            comp_rows = []
            for i,p in enumerate(props):
                comp_rows.append({"Figura": p["name"], "Área con signo": p["A"],
                                  "Centroide x": p["cx"], "Centroide y": p["cy"],
                                  "Ix propio con signo": p["Ix"], "Iy propio con signo": p["Iy"],
                                  "Ixy propio con signo": p["Ixy"]})
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

        st.markdown("**Comprobación de ingeniería**")
        st.write(f"- Diferencia entre la suma de momentos principales y los momentos centroidales: "
                 f"{(res['Imax'] + res['Imin']) - (res['Ix'] + res['Iy']):.3e}. Debe ser aproximadamente cero.")
        st.write(f"- Producto de inercia en los ejes principales: aproximadamente cero por definición.")
        st.write(f"- Determinante de la matriz de inercia: {res['Ix']*res['Iy'] - res['Ixy']**2:.6g}; "
                 "debe ser no negativo, salvo pequeños errores de redondeo.")
        csv = pd.DataFrame([{"Área":res["A"], "x̄":res["cx"], "ȳ":res["cy"],
                             "Ix":res["Ix"], "Iy":res["Iy"], "Ixy":res["Ixy"],
                             "Imax":res["Imax"], "Imin":res["Imin"],
                             "Ángulo Imax (grados)":res["theta"]}]).to_csv(index=False).encode("utf-8")
        st.download_button("Descargar resultados CSV", data=csv, file_name="resultados_inercia.csv",
                           mime="text/csv")
    except Exception as e:
        st.error(f"No se pudo calcular la sección: {e}")

with st.expander("Fórmulas y alcance del modelo"):
    st.markdown(r"""
**Centroide de una sección compuesta**

\[
\bar{x}=\frac{\sum A_i x_i}{\sum A_i},\qquad
\bar{y}=\frac{\sum A_i y_i}{\sum A_i}
\]

**Traslado a los ejes centroidales (Steiner)**

\[
I_x=\sum [I_{x_i}+A_i(y_i-\bar y)^2]
\]
\[
I_y=\sum [I_{y_i}+A_i(x_i-\bar x)^2]
\]
\[
I_{xy}=\sum [I_{xy_i}+A_i(x_i-\bar x)(y_i-\bar y)]
\]

**Momentos principales**

\[
I_{\max,\min}=\frac{I_x+I_y}{2}\pm
\sqrt{\left(\frac{I_x-I_y}{2}\right)^2+I_{xy}^2}
\]

El ángulo mostrado se calcula como
\[
\theta_p=\frac12\operatorname{atan2}(-2I_{xy},I_x-I_y)
\]
bajo la convención \(I_{xy}=\int xy\,dA\).

**Alcance y limitaciones:** las figuras poligonales deben ser simples (sin autointersecciones). Los huecos se modelan como componentes de área negativa y deben estar geométricamente dentro de la sección que se desea vaciar. La aplicación comprueba el área neta y los momentos, pero no detecta automáticamente todos los solapes, huecos fuera del contorno ni autointersecciones. Para secciones con solapes entre componentes positivos, la superposición se cuenta más de una vez: modela las piezas sin solaparlas o resta explícitamente el solape.
""")

st.divider()
st.caption("Herramienta educativa. Verifica los resultados con un cálculo manual conocido antes de emplearlos en un diseño real.")
