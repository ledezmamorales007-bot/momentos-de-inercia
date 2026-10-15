import streamlit as st
import numpy as np
import pandas as pd
import math

# ============================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================================

st.set_page_config(
    page_title="Momentos de Inercia",
    page_icon="📐",
    layout="wide"
)

st.title("Calculadora de Áreas Compuestas y Momentos de Inercia")

st.write(
    "Introduce las figuras que componen la sección. "
    "Usa signo positivo para el material y negativo para los huecos."
)

st.info(
    "Las coordenadas X e Y representan la posición del centroide "
    "de cada figura respecto al origen elegido."
)

# ============================================================
# IMPORTAR IMAGEN DE REFERENCIA
# ============================================================

st.subheader("1. Imagen de la sección")

imagen = st.file_uploader(
    "Sube una imagen de tu figura geométrica",
    type=["png", "jpg", "jpeg"]
)

if imagen is not None:
    st.image(
        imagen,
        caption="Imagen de referencia de la sección",
        use_container_width=True
    )

st.caption(
    "La imagen sirve como referencia visual. "
    "Introduce manualmente las dimensiones y coordenadas."
)

# ============================================================
# TABLA DE ENTRADA
# ============================================================

st.subheader("2. Datos de las figuras")

datos_iniciales = pd.DataFrame([
    {
        "Tipo": "Rectángulo",
        "Signo": 1,
        "b": 10.0,
        "h": 5.0,
        "r": 1.0,
        "x": 5.0,
        "y": 2.5
    },
    {
        "Tipo": "Triángulo rectángulo",
        "Signo": 1,
        "b": 4.0,
        "h": 3.0,
        "r": 1.0,
        "x": 2.0,
        "y": 6.0
    }
])

if "figuras" not in st.session_state:
    st.session_state.figuras = datos_iniciales

figuras = st.data_editor(
    st.session_state.figuras,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="tabla_figuras",
    column_config={
        "Tipo": st.column_config.SelectboxColumn(
            "Tipo de figura",
            options=[
                "Rectángulo",
                "Cuadrado",
                "Triángulo rectángulo",
                "Círculo",
                "Semicírculo",
                "Cuarto de círculo"
            ],
            required=True
        ),
        "Signo": st.column_config.SelectboxColumn(
            "Signo",
            options=[1, -1],
            required=True
        ),
        "b": st.column_config.NumberColumn(
            "Base b",
            min_value=0.0,
            step=0.5
        ),
        "h": st.column_config.NumberColumn(
            "Altura h",
            min_value=0.0,
            step=0.5
        ),
        "r": st.column_config.NumberColumn(
            "Radio r",
            min_value=0.0,
            step=0.5
        ),
        "x": st.column_config.NumberColumn(
            "Coordenada X",
            step=0.5
        ),
        "y": st.column_config.NumberColumn(
            "Coordenada Y",
            step=0.5
        )
    }
)

st.session_state.figuras = figuras

st.caption(
    "b y h son las dimensiones de cada figura; r es el radio. "
    "Las coordenadas X e Y corresponden a su centroide."
)

# ============================================================
# FUNCIONES GEOMÉTRICAS
# ============================================================

def propiedades(tipo, b, h, r):
    """
    Devuelve:
    A   = área positiva
    Ix  = inercia centroidal respecto al eje horizontal
    Iy  = inercia centroidal respecto al eje vertical
    Ixy = producto de inercia centroidal

    Para el triángulo rectángulo se supone el ángulo recto
    en la esquina inferior izquierda.

    Para el semicírculo se supone que su diámetro es horizontal.
    Para el cuarto de círculo se supone que está en el primer
    cuadrante de sus ejes locales.
    """

    if tipo == "Rectángulo":
        if b <= 0 or h <= 0:
            raise ValueError("El rectángulo requiere b y h positivos.")

        A = b * h
        Ix = b * h**3 / 12
        Iy = h * b**3 / 12
        Ixy = 0.0

    elif tipo == "Cuadrado":
        lado = b if b > 0 else h

        if lado <= 0:
            raise ValueError("El cuadrado requiere un lado positivo.")

        A = lado**2
        Ix = lado**4 / 12
        Iy = lado**4 / 12
        Ixy = 0.0

    elif tipo == "Triángulo rectángulo":
        if b <= 0 or h <= 0:
            raise ValueError(
                "El triángulo requiere base y altura positivas."
            )

        A = b * h / 2
        Ix = b * h**3 / 36
        Iy = h * b**3 / 36
        Ixy = -(b**2 * h**2) / 72

    elif tipo == "Círculo":
        if r <= 0:
            raise ValueError("El círculo requiere un radio positivo.")

        A = math.pi * r**2
        Ix = math.pi * r**4 / 4
        Iy = math.pi * r**4 / 4
        Ixy = 0.0

    elif tipo == "Semicírculo":
        if r <= 0:
            raise ValueError(
                "El semicírculo requiere un radio positivo."
            )

        A = math.pi * r**2 / 2

        distancia = 4 * r / (3 * math.pi)

        Ix = math.pi * r**4 / 8 - A * distancia**2
        Iy = math.pi * r**4 / 8
        Ixy = 0.0

    elif tipo == "Cuarto de círculo":
        if r <= 0:
            raise ValueError(
                "El cuarto de círculo requiere un radio positivo."
            )

        A = math.pi * r**2 / 4

        distancia = 4 * r / (3 * math.pi)

        Ix = math.pi * r**4 / 16 - A * distancia**2
        Iy = math.pi * r**4 / 16 - A * distancia**2

        Ixy = r**4 / 8 - A * distancia**2

    else:
        raise ValueError("Tipo de figura no reconocido.")

    return A, Ix, Iy, Ixy


# ============================================================
# VALIDAR Y CALCULAR LAS FIGURAS
# ============================================================

st.subheader("3. Resultados por figura")

resultados = []
errores = []

for indice, fila in figuras.iterrows():

    try:
        tipo = str(fila["Tipo"])
        signo = int(fila["Signo"])

        if signo not in (1, -1):
            raise ValueError("El signo debe ser +1 o -1.")

        b = float(fila["b"])
        h = float(fila["h"])
        r = float(fila["r"])
        x = float(fila["x"])
        y = float(fila["y"])

        if not all(
            math.isfinite(v)
            for v in (b, h, r, x, y)
        ):
            raise ValueError("Hay valores no válidos.")

        A, Ix, Iy, Ixy = propiedades(tipo, b, h, r)

        # Área algebraica
        As = signo * A

        # Inercias propias con signo
        Ixs = signo * Ix
        Iys = signo * Iy
        Ixys = signo * Ixy

        # Teorema de Steiner respecto al origen global
        Ix_global = Ixs + As * y**2
        Iy_global = Iys + As * x**2
        Ixy_global = Ixys + As * x * y

        resultados.append({
            "Figura": indice + 1,
            "Tipo": tipo,
            "Signo": signo,
            "Base b": b,
            "Altura h": h,
            "Radio r": r,
            "Área algebraica": As,
            "Xi": x,
            "Yi": y,
            "AiXi": As * x,
            "AiYi": As * y,
            "Ix propio": Ixs,
            "Iy propio": Iys,
            "Ixy propio": Ixys,
            "Ix global": Ix_global,
            "Iy global": Iy_global,
            "Ixy global": Ixy_global
        })

    except (ValueError, TypeError, KeyError) as error:
        errores.append(
            f"Fila {indice + 1}: {error}"
        )

if errores:
    st.warning(
        "Revisa los siguientes datos antes de continuar:\n\n"
        + "\n".join(errores)
    )

if resultados and not errores:

    tabla = pd.DataFrame(resultados)

    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # CENTROIDE DE LA SECCIÓN COMPUESTA
    # ========================================================

    st.subheader("4. Centroide de la sección")

    At = tabla["Área algebraica"].sum()

    if abs(At) < 1e-12:
        st.error(
            "El área algebraica total es cero. "
            "No se puede calcular el centroide."
        )

    else:
        Xc = tabla["AiXi"].sum() / At
        Yc = tabla["AiYi"].sum() / At

        col1, col2, col3 = st.columns(3)

        col1.metric("Área total", f"{At:.6f}")
        col2.metric("Centroide X", f"{Xc:.6f}")
        col3.metric("Centroide Y", f"{Yc:.6f}")

        # ====================================================
        # INERCIAS RESPECTO AL CENTROIDE
        # ====================================================

        st.subheader("5. Momentos de inercia centroidales")

        Ix0 = tabla["Ix global"].sum()
        Iy0 = tabla["Iy global"].sum()
        Ixy0 = tabla["Ixy global"].sum()

        Ixc = Ix0 - At * Yc**2
        Iyc = Iy0 - At * Xc**2
        Ixyc = Ixy0 - At * Xc * Yc

        col1, col2, col3 = st.columns(3)

        col1.metric("Ix centroidal", f"{Ixc:.6f}")
        col2.metric("Iy centroidal", f"{Iyc:.6f}")
        col3.metric("Ixy centroidal", f"{Ixyc:.6f}")

        # ====================================================
        # MOMENTOS PRINCIPALES
        # ====================================================

        st.subheader("6. Momentos principales de inercia")

        promedio = (Ixc + Iyc) / 2

        radio = math.sqrt(
            ((Ixc - Iyc) / 2)**2 + Ixyc**2
        )

        Imax = promedio + radio
        Imin = promedio - radio

        # Convención:
        # Ixy = integral de x*y dA
        # theta = orientación del eje principal de Imax
        theta = 0.5 * math.atan2(
            -2 * Ixyc,
            Ixc - Iyc
        )

        theta_grados = math.degrees(theta)

        col1, col2, col3 = st.columns(3)

        col1.metric("I máximo", f"{Imax:.6f}")
        col2.metric("I mínimo", f"{Imin:.6f}")
        col3.metric("Ángulo principal", f"{theta_grados:.4f}°")

        st.write(
            "El ángulo indicado corresponde a la orientación "
            "de un eje principal asociado a I máximo, medido "
            "desde el eje X positivo según la convención "
            "utilizada en el programa."
        )

        # ====================================================
        # TABLA RESUMEN
        # ====================================================

        st.subheader("7. Resumen final")

        resumen = pd.DataFrame({
            "Magnitud": [
                "Área algebraica total",
                "Centroide X",
                "Centroide Y",
                "Ix centroidal",
                "Iy centroidal",
                "Ixy centroidal",
                "Momento principal máximo",
                "Momento principal mínimo",
                "Ángulo principal"
            ],
            "Resultado": [
                At,
                Xc,
                Yc,
                Ixc,
                Iyc,
                Ixyc,
                Imax,
                Imin,
                theta_grados
            ]
        })

        st.dataframe(
            resumen,
            use_container_width=True,
            hide_index=True
        )

        # ====================================================
        # DESCARGAR RESULTADOS SIN CREAR CARPETAS
        # ====================================================

        st.subheader("8. Exportar resultados")

        csv = tabla.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="Descargar tabla de resultados CSV",
            data=csv,
            file_name="resultados_momentos_inercia.csv",
            mime="text/csv"
        )

else:
    st.info(
        "Introduce al menos una figura válida para calcular "
        "los resultados."
    )

# ============================================================
# NOTA FINAL
# ============================================================

st.divider()

st.caption(
    "Calculadora de áreas compuestas y momentos de inercia. "
    "Verifica las unidades y la geometría de cada figura "
    "antes de utilizar los resultados en un cálculo de ingeniería."
)
