# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/vistas/cocina.py
# Librerías: streamlit, pandas; servicios, calculo, estructuras, busqueda (propios)
# ---------------------------------------------------------------------
# Interfaz operativa del perfil COCINA (Actividad 3).
# Regla de oro: acá no aparece ningún costo, precio ni merma. Para lograrlo
# todo lo que se muestra sale de resultado.vista_cocina() y de consultas
# que ni siquiera piden columnas con plata (ver base_datos.obtener_ordenes_cocina).
# =====================================================================

import pandas as pd
import streamlit as st

from src.base_datos import ErrorBaseDatos
from src.busqueda import buscar_secuencial
from src.calculo import calcular_orden
from src.estructuras import Pila
from src.servicios import registrar_orden
from src.vistas.componentes import (
    formatear_fechas, formulario_servicio, mostrar_orden_cocina, tabla_cocina,
)


def _pila_sesion():
    """
    Pila (LIFO) con las órdenes registradas en esta sesión. Se usa una pila
    porque lo que le interesa a cocina es lo ÚLTIMO que ingresó, y al
    recorrerla sale primero la más reciente.
    """
    if "pila_ordenes" not in st.session_state:
        st.session_state["pila_ordenes"] = Pila()
    return st.session_state["pila_ordenes"]


def pagina_nueva_orden(repo, usuario, recetas):
    """Formulario de solicitud de servicio + orden de preparación + guardado automático."""
    st.header("Nueva orden de preparación")
    st.write("Seleccione el menú y la cantidad de comensales. La orden se calcula y se guarda automáticamente.")

    solicitud = formulario_servicio(recetas, "cocina")

    if solicitud is False:                      # formulario con errores: no mostramos la orden anterior
        st.session_state.pop("ultima_orden", None)
    elif solicitud is not None:
        receta, comensales = solicitud
        try:
            orden_id, resultado = registrar_orden(repo, usuario, receta, comensales)
        except ErrorBaseDatos as e:
            st.error(str(e))
            return
        st.session_state["ultima_orden"] = (orden_id, resultado)
        _pila_sesion().apilar({"orden": orden_id, "menu": receta.nombre, "comensales": comensales})

    ultima = st.session_state.get("ultima_orden")
    if ultima is not None:
        mostrar_orden_cocina(*ultima)

    pila = _pila_sesion()
    if len(pila) > 0:
        st.divider()
        st.markdown("**Órdenes ingresadas en esta sesión** (la más reciente arriba)")
        filas = [{"N° orden": p["orden"], "Menú": p["menu"], "Comensales": p["comensales"]} for p in pila]
        st.dataframe(pd.DataFrame(filas), hide_index=True)


def pagina_historial(repo, usuario, recetas):
    """
    Historial de órdenes (solo número, fecha, menú y comensales) y posibilidad
    de volver a ver la lista de preparación de una orden anterior.
    """
    st.header("Historial de órdenes")
    filas = repo.obtener_ordenes_cocina(limite=50)
    if not filas:
        st.info("Todavía no hay órdenes registradas.")
        return

    df = pd.DataFrame(filas)
    # Cambio el id del menú por su nombre usando búsqueda secuencial en el catálogo
    nombres = []
    for receta_id in df["receta_id"]:
        receta = buscar_secuencial(recetas, lambda r: r.id == receta_id)
        nombres.append(receta.nombre if receta else f"Menú #{receta_id}")
    tabla = pd.DataFrame({
        "N° orden": df["id"],
        "Fecha": formatear_fechas(df["fecha"]),
        "Menú": nombres,
        "Comensales": df["comensales"],
    })
    st.dataframe(tabla, hide_index=True)

    st.subheader("Ver lista de preparación de una orden")
    elegida = st.selectbox("N° de orden", list(df["id"]), index=None, placeholder="Seleccione una orden...")
    if elegida is not None:
        fila = buscar_secuencial(filas, lambda f: f["id"] == elegida)
        receta = buscar_secuencial(recetas, lambda r: r.id == fila["receta_id"])
        if receta is not None:
            # Las cantidades no dependen de costos, así que se vuelven a calcular sin consultar plata
            resultado = calcular_orden(receta, fila["comensales"])
            st.markdown(f"**{receta.nombre}** · {fila['comensales']} comensales")
            tabla_cocina(resultado)
