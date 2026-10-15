import os, textwrap
code = r'''import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Momentos de Inercia | Figuras Compuestas",
    page_icon="📐",
    layout="wide"
)

st.title("📐 Calculadora de centroides y momentos de inercia")
st.caption("Ingeniería Civil · Figuras compuestas por rectángulos y triángulos no rotados")

st.info(
    "Introduce las dimensiones y selecciona la esquina de cada triángulo. "
    "El signo positivo suma material y el negativo representa un hueco que se resta."
)

st.sidebar.header("⚙️ Configuración")
unidad = st.sidebar.selectbox("Unidad de longitud", ["cm", "mm", "m"], index=0)
st.sidebar.markdown("**Sistema de referencia**")
st.sidebar.write("Origen en la esquina inferior izquierda del rectángulo principal.")
st.sidebar.write("X positivo hacia la derecha; Y positivo hacia arriba.")

st.subheader("1. Dimensiones del rectángulo principal")
c1, c2 = st.columns(2)
with c1:
    B = st.number_input("Base del rectángulo", min_value=0.001, value=8.0, step=0.5)
with c2:
    H = st.number_input("Altura del rectángulo", min_value=0.001, value=9.0, step=0.5)

st.subheader("2. Figuras que se suman o se restan")
st.write("Las tres filas iniciales reproducen el ejemplo que describiste. Puedes cambiar dimensiones, signo y ubicación.")

if "n_figuras" not in st.session_state:
    st.session_state.n_figuras = 3

defaults = [
    {"tipo": "Rectángulo principal", "signo": "+", "base": 8.0, "altura": 9.0, "ubicacion": "Rectángulo principal"},
    {"tipo": "Triángulo rectángulo", "signo": "−", "base": 4.0, "altura": 6.0, "ubicacion": "Superior izquierda"},
    {"tipo": "Triángulo rectángulo", "signo": "−", "base": 8.0, "altura": 3.0, "ubicacion": "Inferior derecha"},
]
locations = ["Superior izquierda", "Superior derecha", "Inferior izquierda", "Inferior derecha"]

figures = []
for i in range(st.session_state.n_figuras):
    d = defaults[i] if i < len(defaults) else {
        "tipo": "Triángulo rectángulo", "signo": "+", "base": 1.0, "altura": 1.0, "ubicacion": "Inferior izquierda"
    }
    with st.expander(f"Figura {i+1}", expanded=(i < 3)):
        a, b, c, e = st.columns(4)
        with a:
            tipo = st.selectbox("Tipo", ["Rectángulo principal", "Rectángulo", "Triángulo rectángulo"], index=["Rectángulo principal", "Rectángulo", "Triángulo rectángulo"].index(d["tipo"]) if d["tipo"] in ["Rectángulo principal", "Rectángulo", "Triángulo rectángulo"] else 2, key=f"tipo_{i}")
        with b:
            signo = st.selectbox("Signo", ["+", "−"], index=0 if d["signo"] == "+" else 1, key=f"signo_{i}")
        with c:
            base = st.number_input(f"Base ({unidad})", min_value=0.001, value=float(d["base"]), step=0.5, key=f"base_{i}")
        with e:
            altura = st.number_input(f"Altura ({unidad})", min_value=0.001, value=float(d["altura"]), step=0.5, key=f"altura_{i}")

        if tipo == "Rectángulo principal":
            ubicacion = "Rectángulo principal"
            st.caption("Este rectángulo define el contorno de referencia y se coloca con su esquina inferior izquierda en (0, 0).")
        else:
            if tipo == "Rectángulo":
                ubicaciones_rect = ["Inferior izquierda", "Inferior derecha", "Superior izquierda", "Superior derecha"]
                ubicacion = st.selectbox("Esquina de referencia", ubicaciones_rect, index=0, key=f"ubic_{i}")
            else:
                ubicacion = st.selectbox("Esquina del triángulo", locations, index=locations.index(d["ubicacion"]) if d["ubicacion"] in locations else 0, key=f"ubic_{i}")
            st.caption("La base se extiende horizontalmente desde la esquina elegida y la altura verticalmente hacia el interior del rectángulo.")

        figures.append({"tipo": tipo, "signo": signo, "base": float(base), "altura": float(altura), "ubicacion": ubicacion})

col_add, col_remove = st.columns(2)
with col_add:
    if st.button("➕ Añadir figura"):
        st.session_state.n_figuras += 1
        st.rerun()
with col_remove:
    if st.button("➖ Quitar última figura", disabled=st.session_state.n_figuras <= 1):
        st.session_state.n_figuras -= 1
        st.rerun()

def signed(sign):
    return 1.0 if sign == "+" else -1.0

def calc_figure(f, B, H):
    b, h = f["base"], f["altura"]
    tipo, loc = f["tipo"], f["ubicacion"]
    s = signed(f["signo"])
    if tipo == "Rectángulo principal":
        b, h = B, H
        x0, y0 = 0.0, 0.0
        area = b*h
        xc, yc = x0+b/2, y0+h/2
        ix_c = b*h**3/12
        iy_c = h*b**3/12
    elif tipo == "Rectángulo":
        if loc == "Inferior izquierda":
            x0, y0 = 0.0, 0.0
        elif loc == "Inferior derecha":
            x0, y0 = B-b, 0.0
        elif loc == "Superior izquierda":
            x0, y0 = 0.0, H-h
        else:
            x0, y0 = B-b, H-h
        area = b*h
        xc, yc = x0+b/2, y0+h/2
        ix_c = b*h**3/12
        iy_c = h*b**3/12
    else:
        # Triángulo rectángulo con catetos b y h, colocado en la esquina elegida.
        if loc == "Superior izquierda":
            x0, y0 = 0.0, H-h
            xc, yc = x0+b/3, y0+2*h/3
        elif loc == "Superior derecha":
            x0, y0 = B-b, H-h
            xc, yc = x0+2*b/3, y0+2*h/3
        elif loc == "Inferior izquierda":
            x0, y0 = 0.0, 0.0
            xc, yc = x0+b/3, y0+h/3
        else:
            x0, y0 = B-b, 0.0
            xc, yc = x0+2*b/3, y0+h/3
        area = b*h/2
        # Inercias centroidales de un triángulo rectángulo respecto a ejes paralelos a sus catetos.
        ix_c = b*h**3/36
        iy_c = h*b**3/36

    return {
        "Tipo de figura": tipo,
        "Figura (+/−)": f["signo"],
        f"Base ({unidad})": b,
        f"
