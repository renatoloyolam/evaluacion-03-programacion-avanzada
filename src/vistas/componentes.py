# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/vistas/componentes.py
# Librerías: streamlit, pandas; calculo, busqueda (propios)
# ---------------------------------------------------------------------
# Piezas de interfaz que usan tanto cocina como administrador:
# el formulario de solicitud de servicio (con validaciones) y las tablas
# de la orden. Acá no hay cuentas ni consultas a la BD, solo pantalla.
# =====================================================================

import pandas as pd
import streamlit as st

from src.busqueda import buscar_por_texto
from src.calculo import (
    formato_clp, redondear, texto_cantidad_receta, texto_envases, validar_comensales, validar_menu,
)


def formulario_servicio(recetas, clave):
    """
    Formulario de solicitud de servicio: tipo de menú + cantidad de comensales.
    Devuelve:
      - None            si todavía no se presionó el botón,
      - False           si se presionó pero hay errores (se muestran en pantalla),
      - (receta, n)     si todo está válido.

    Decisión: el campo de comensales NO tiene min_value, a propósito. Si lo
    tuviera, el propio widget impediría escribir 0 o negativos y no se vería
    la validación del programa. Así el usuario puede equivocarse y el sistema
    le explica qué pasó. El campo parte vacío (value=None) para poder detectar nulos,
    y es de tipo decimal (step=1.0) para que, si escriben 2.5, la validación lo rechace
    con un mensaje en vez de que el widget lo redondee en silencio.
    """
    with st.form(f"form_servicio_{clave}"):
        nombres = [r.nombre for r in recetas]
        menu = st.selectbox("Tipo de menú", nombres, index=None, placeholder="Seleccione un menú...")
        comensales = st.number_input(
            "Cantidad de comensales", value=None, step=1.0, format="%g", placeholder="Ej: 25",
            help="Número entero mayor que cero.",
        )
        enviado = st.form_submit_button("Calcular y registrar orden", type="primary")

    if not enviado:
        return None

    errores = []
    receta = None
    try:
        receta = validar_menu(buscar_por_texto(recetas, lambda r: r.nombre, menu) if menu else None)
    except ValueError as e:
        errores.append(str(e))
    cantidad = None
    try:
        cantidad = validar_comensales(comensales)
    except ValueError as e:
        errores.append(str(e))

    if errores:
        for e in errores:
            st.error(e)
        return False
    return receta, cantidad


def formatear_fechas(serie):
    """Pasa fechas ISO de Supabase (UTC) a hora de Chile con formato dd-mm-aaaa hh:mm."""
    fechas = pd.to_datetime(serie, utc=True, format="ISO8601").dt.tz_convert("America/Santiago")
    return fechas.dt.strftime("%d-%m-%Y %H:%M")


def tabla_cocina(resultado):
    """Tabla para el perfil cocina: SOLO ingrediente y cantidades. Sin costos ni mermas."""
    filas = []
    for l in resultado.vista_cocina():
        filas.append({
            "Ingrediente": l.ingrediente,
            "Cantidad a preparar": texto_cantidad_receta(l.cantidad_preparar, l.unidad_receta),
            "Cantidad requerida": texto_envases(l.envases, l.unidad_compra),
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True)


def mostrar_orden_cocina(orden_id, resultado):
    """Encabezado + tabla de la orden de preparación para cocina."""
    st.success(f"Orden N°{orden_id} registrada correctamente.")
    st.subheader(f"Orden de preparación N°{orden_id}")
    # Se muestra con markdown (no st.metric) porque metric corta con "..." los nombres largos de menú
    st.markdown(f"**Menú:** {resultado.receta.nombre}  \n**Comensales:** {resultado.comensales}")
    tabla_cocina(resultado)
    st.caption("Los productos son indivisibles: la cantidad requerida son envases o unidades completas.")


def mostrar_orden_admin(orden_id, resultado):
    """Vista completa (con plata y mermas) de una orden. Solo para administrador."""
    st.success(f"Orden N°{orden_id} registrada correctamente.")
    st.subheader(f"Orden N°{orden_id}: {resultado.receta.nombre} ({resultado.comensales} comensales)")

    st.markdown("**Lista de preparación (lo que ve cocina)**")
    tabla_cocina(resultado)

    st.markdown("**Detalle económico por ingrediente**")
    filas = []
    for l in resultado.lineas:
        filas.append({
            "Ingrediente": l.ingrediente.nombre,
            "Envases": texto_envases(l.envases, l.ingrediente.unidad_compra),
            "Costo envases ($)": redondear(l.costo_envases, 2),
            "Merma física (envase)": redondear(l.merma_envases, 2),
            "Merma (porciones)": redondear(l.merma_porciones, 2),
            "Pérdida por merma ($)": redondear(l.perdida_merma, 2),
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True)

    a, b, c = st.columns(3)
    a.metric("Costo total", formato_clp(resultado.costo_total))
    b.metric("Costo por plato", formato_clp(resultado.costo_por_plato, 2))
    c.metric("Valor de venta por plato", formato_clp(resultado.precio_venta_plato, 2))
    d, e, f = st.columns(3)
    d.metric("Pérdida por merma", formato_clp(resultado.perdida_merma_total))
    e.metric("Merma física total (envases)", f"{redondear(resultado.merma_fisica_envases, 2):.2f}")
    f.metric("Ingreso proyectado", formato_clp(resultado.ingreso_total))
