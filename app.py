from pathlib import Path
import zipfile, textwrap

base = Path("/mnt/data/figuras_compuestas_streamlit")
base.mkdir(parents=True, exist_ok=True)

app_code = r'''import streamlit as st
import numpy as np
import pandas as pd
import cv2
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Áreas compuestas e inercias", layout="wide")
st.title("Calculadora de áreas compuestas y momentos de inercia")
st.caption("Prototipo: ingreso manual + detección experimental de contornos en una imagen.")

st.warning(
    "La detección por imagen es una ayuda experimental: identifica contornos aproximados, "
    "pero no interpreta de forma fiable las cotas escritas ni sabe siempre qué líneas son ejes, "
    "cotas o bordes reales. Revisa y corrige los datos antes de usar los resultados."
)

def detect_shapes(pil_img, min_area_px, epsilon_factor, threshold_mode):
    rgb = np.array(pil_img.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    if threshold_mode == "Canny (recomendado)":
        edges = cv2.Canny(gray, 50, 150)
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    else:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    h, w = gray.shape
    found = []
    annotated = rgb.copy()
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area_px or area > 0.95 * w * h:
            continue
        peri = cv2.arcLength(c, True)
        if peri <= 0:
            continue
        approx = cv2.approxPolyDP(c, epsilon_factor * peri, True)
        n = len(approx)
        x, y, bw, bh = cv2.boundingRect(approx)
        if bw < 8 or bh < 8:
            continue

        if n == 3:
            kind = "Triángulo rectángulo (aprox.)"
            points = approx.reshape(-1, 2)
            # Clasificación experimental: comprobar si algún ángulo es cercano a 90 grados.
            right = False
            for i in range(3):
                p0 = points[i].astype(float)
                p1 = points[(i + 1) % 3].astype(float)
                p2 = points[(i + 2) % 3].astype(float)
                v1, v2 = p1 - p0, p2 - p0
                denom = np.linalg.norm(v1) * np.linalg.norm(v2)
                if denom > 0 and abs(np.dot(v1, v2) / denom) < 0.22:
                    right = True
            if not right:
                kind = "Triángulo (revisar)"
        elif n == 4:
            # Cuadrilátero aproximado: se propone rectángulo, pero requiere confirmación.
            kind = "Rectángulo (revisar)"
        else:
            continue

        found.append({
            "tipo_detectado": kind,
            "x_px": int(x), "y_px_desde_arriba": int(y),
            "ancho_px": int(bw), "alto_px": int(bh),
            "area_contorno_px2": round(float(area), 1),
            "vertices": n,
            "_contour": approx
        })

    # Eliminar duplicados muy parecidos producidos por bordes dobles.
    filtered = []
    found.sort(key=lambda d: d["area_contorno_px2"], reverse=True)
    for item in found:
        duplicate = False
        for old in filtered:
            if (abs(item["x_px"] - old["x_px"]) < 5 and
                abs(item["y_px_desde_arriba"] - old["y_px_desde_arriba"]) < 5 and
                abs(item["ancho_px"] - old["ancho_px"]) < 8 and
                abs(item["alto_px"] - old["alto_px"]) < 8):
                duplicate = True
                break
        if not duplicate:
            filtered.append(item)

    for i, item in enumerate(filtered):
        cv2.drawContours(annotated, [item["_contour"]], -1, (255, 0, 0), 2)
        cv2.putText(annotated, str(i + 1),
                    (item["x_px"], max(18, item["y_px_desde_arriba"] - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 120, 255), 2)
    for item in filtered:
        item.pop("_contour", None)
    return annotated, filtered

def calculate_properties(df):
    rows = []
    for _, r in df.iterrows():
        kind = str(r["tipo"])
        b = float(r["base"])
        h = float(r["altura"])
        x0 = float(r["x"])
        y0 = float(r["y"])
        sign = float(r["signo"])
        if b <= 0 or h <= 0:
            continue

        if kind == "Rectángulo":
            A = b * h
            xc, yc = x0 + b/2, y0 + h/2
            Ix_c = b * h**3 / 12
            Iy_c = h * b**3 / 12
        elif kind == "Triángulo rectángulo":
            A = b * h / 2
            # El vértice recto se supone en la esquina inferior izquierda del cuadro.
            xc, yc = x0 + b/3, y0 + h/3
            Ix_c = b * h**3 / 36
            Iy_c = h * b**3 / 36
        else:
            continue

        rows.append({
            "tipo": kind, "signo": sign, "A_firmada": sign*A,
            "x_c": xc, "y_c": yc,
            "Ix_c_local": Ix_c, "Iy_c_local": Iy_c,
            "Ix_origen": sign*(Ix_c + A*(yc**2)),
            "Iy_origen": sign*(Iy_c + A*(xc**2)),
            "Ixy_origen": sign*A*xc*yc
        })

    if not rows:
        return None, None
    detail = pd.DataFrame(rows)
    A_total = detail["A_firmada"].sum()
    if abs(A_total) < 1e-10:
        return detail, {"error": "El área total es cero. Revisa los signos y las dimensiones."}
    xbar = (detail["A_firmada"] * detail["x_c"]).sum() / A_total
    ybar = (detail["A_firmada"] * detail["y_c"]).sum() / A_total
    Ix_o = detail["Ix_origen"].sum()
    Iy_o = detail["Iy_origen"].sum()
    Ixy_o = detail["Ixy_origen"].sum()
    Ix = Ix_o - A_total*ybar**2
    Iy = Iy_o - A_total*xbar**2
    Ixy = Ixy_o - A_total*xbar*ybar
    mean = (Ix + Iy)/2
    rad = np.sqrt(max(0, ((Ix - Iy)/2)**2 + Ixy**2))
    I1, I2 = mean + rad, mean - rad
    result = {
        "Área total": A_total, "Centroide x̄": xbar, "Centroide ȳ": ybar,
        "Ix centroidal": Ix, "Iy centroidal": Iy, "Ixy centroidal": Ixy,
        "Momento principal I1": I1, "Momento principal I2": I2
    }
    return detail, result

tab_img, tab_manual = st.tabs(["📷 Reconocimiento por imagen (experimental)", "✍️ Ingreso manual"])

with tab_img:
    st.subheader("1. Sube una fotografía o captura")
    upload = st.file_uploader("Imagen de la sección compuesta", type=["png", "jpg", "jpeg", "webp"], key="img")
    if upload:
        pil_img = Image.open(upload).convert("RGB")
        col1, col2 = st.columns(2)
        with col1:
            st.image(pil_img, caption="Imagen original", use_container_width=True)
        with col2:
            st.markdown("**Ajustes de detección**")
            threshold_mode = st.selectbox("Método", ["Canny (recomendado)", "Umbral automático"])
            min_area = st.slider("Área mínima del contorno (píxeles²)", 100, 10000, 500, 100)
            epsilon = st.slider("Tolerancia de aproximación", 0.005, 0.08, 0.025, 0.005)
            scale = st.number_input("Escala: unidades reales por píxel", min_value=0.0001, value=0.1, step=0.1,
                                    help="Ejemplo: si 100 píxeles representan 10 cm, escribe 0.1 cm/píxel.")
            axis_x = st.number_input("Coordenada x del origen en la imagen (píxeles)", min_value=0.0, value=0.0, step=1.0)
            axis_y = st.number_input("Coordenada y del origen en la imagen (píxeles desde arriba)", min_value=0.0, value=0.0, step=1.0)
        annotated, shapes = detect_shapes(pil_img, min_area, epsilon, threshold_mode)
        st.image(annotated, caption="Contornos propuestos: revisa si coinciden con las figuras reales", use_container_width=True)
        if not shapes:
            st.info("No se detectaron polígonos claros. Prueba una imagen más nítida o usa el ingreso manual.")
        else:
            st.write(f"Contornos candidatos encontrados: **{len(shapes)}**. No todos necesariamente son figuras de la sección.")
            st.dataframe(pd.DataFrame(shapes), use_container_width=True, hide_index=True)
            st.subheader("2. Prepara una tabla corregible")
            st.caption(
                "La detección no lee las cotas escritas. Las medidas iniciales se estiman a partir de píxeles y de la escala indicada. "
                "Corrige tipo, base, altura y coordenadas. Las coordenadas x e y corresponden a la esquina inferior izquierda "
                "del rectángulo envolvente; el triángulo se supone con ángulo recto en esa esquina."
            )
            editable = []
            for i, s in enumerate(shapes):
                kind = "Triángulo rectángulo" if s["tipo_detectado"].startswith("Triángulo") else "Rectángulo"
                b = s["ancho_px"] * scale
                h = s["alto_px"] * scale
                x = (s["x_px"] - axis_x) * scale
                y = (pil_img.height - (s["y_px_desde_arriba"] + s["alto_px"]) - (pil_img.height-axis_y)) * scale
                # y above is expressed relative to the selected pixel-origin, with positive y upward.
                y = (axis_y - (s["y_px_desde_arriba"] + s["alto_px"])) * scale
                editable.append({"incluir": True, "tipo": kind, "base": round(b, 3), "altura": round(h, 3),
                                 "x": round(x, 3), "y": round(y, 3), "signo": 1.0})
            edf = pd.DataFrame(editable)
            edited = st.data_editor(
                edf, use_container_width=True, hide_index=True, num_rows="dynamic",
                column_config={
                    "incluir": st.column_config.CheckboxColumn("Incluir"),
                    "tipo": st.column_config.SelectboxColumn("Tipo", options=["Rectángulo", "Triángulo rectángulo"]),
                    "base": st.column_config.NumberColumn("Base", min_value=0.0),
                    "altura": st.column_config.NumberColumn("Altura", min_value=0.0),
                    "x": st.column_config.NumberColumn("x esquina inferior izquierda"),
                    "y": st.column_config.NumberColumn("y esquina inferior izquierda"),
                    "signo": st.column_config.SelectboxColumn("Signo (+ material / - hueco)", options=[1.0, -1.0])
                }
            )
            chosen = edited[edited["incluir"]].drop(columns=["incluir"])
            if st.button("Calcular propiedades de la imagen", type="primary"):
                detail, result = calculate_properties(chosen)
                if result is None:
                    st.error("No hay figuras válidas para calcular.")
                elif "error" in result:
                    st.error(result["error"])
                else:
                    st.success("Cálculo realizado con los datos de la tabla corregida.")
                    st.dataframe(pd.DataFrame([result]), use_container_width=True)
                    st.subheader("Contribución de cada figura")
                    st.dataframe(detail, use_container_width=True, hide_index=True)
    else:
        st.info("Sube una imagen para probar la detección. Para dibujos difíciles, usa el modo manual.")

with tab_manual:
    st.subheader("Ingreso manual de figuras")
    st.caption("Coordenadas x e y de la esquina inferior izquierda. Las figuras se suponen sin rotación. Para triángulos, el ángulo recto se ubica en esa esquina.")
    default = pd.DataFrame([
        {"tipo": "Rectángulo", "base": 4.0, "altura": 2.0, "x": 0.0, "y": 0.0, "signo": 1.0},
        {"tipo": "Triángulo rectángulo", "base": 2.0, "altura": 1.0, "x": 4.0, "y": 0.0, "signo": 1.0}
    ])
    manual = st.data_editor(
        default, num_rows="dynamic", use_container_width=True, hide_index=True,
        column_config={
            "tipo": st.column_config.SelectboxColumn("Tipo", options=["Rectángulo", "Triángulo rectángulo"]),
            "base": st.column_config.NumberColumn("Base", min_value=0.0),
            "altura": st.column_config.NumberColumn("Altura", min_value=0.0),
            "x": st.column_config.NumberColumn("x esquina inferior izquierda"),
            "y": st.column_config.NumberColumn("y esquina inferior izquierda"),
            "signo": st.column_config.SelectboxColumn("Signo (+ material / - hueco)", options=[1.0, -1.0])
        }
    )
    if st.button("Calcular propiedades manuales", type="primary"):
        detail, result = calculate_properties(manual)
        if result is None:
            st.error("Introduce al menos una figura con dimensiones positivas.")
        elif "error" in result:
            st.error(result["error"])
        else:
            st.dataframe(pd.DataFrame([result]), use_container_width=True)
            st.subheader("Contribución de cada figura")
            st.dataframe(detail, use_container_width=True, hide_index=True)

st.divider()
st.caption(
    "Convención: x hacia la derecha e y hacia arriba. Los huecos se ingresan con signo -1. "
    "Este prototipo no sustituye la revisión del dibujo ni la comprobación manual de resultados."
)
'''
requirements = """streamlit
numpy
pandas
opencv-python-headless
Pillow
"""

(base / "app.py").write_text(app_code, encoding="utf-8")
(base / "requirements.txt").write_text(requirements, encoding="utf-8")
zip_path = Path("/mnt/data/streamlit_figuras_compuestas_prototipo.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(base / "app.py", arcname="app.py")
    z.write(base / "requirements.txt", arcname="requirements.txt")

print("Archivos creados:")
print(base / "app.py")
print(base / "requirements.txt")
print(zip_path)
