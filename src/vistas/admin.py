# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/vistas/admin.py
# Librerías: streamlit, pandas, altair; analisis, calculo, autenticacion (propios)
# ---------------------------------------------------------------------
# Panel gerencial del perfil ADMINISTRADOR (Actividad 4):
#   1) Resumen ejecutivo con KPIs
#   2) Historial filtrable y ordenable de preparaciones
#   3) Análisis de mermas e impacto económico
# Cada función parte llamando a exigir_costos(): aunque alguien lograra
# llegar acá sin ser administrador, el programa corta con un error.
# =====================================================================

import altair as alt
import pandas as pd
import streamlit as st

from src.analisis import (
    calcular_kpis, construir_grafo, filtrar_por_menu, menus_relacionados,
    ordenar_historial, ranking_jerarquico, resumen_por_ingrediente,
    resumen_por_menu, top_ordenes_por_perdida,
)
from src.autenticacion import exigir_costos
from src.base_datos import ErrorBaseDatos
from src.busqueda import filtrar_secuencial
from src.config import TAM_BLOQUE_EXTERNO
from src.ordenamiento import ALGORITMOS_INTERNOS, ordenar
from src.calculo import formato_clp, texto_cantidad_receta, texto_envases
from src.servicios import registrar_orden
from src.vistas.componentes import formatear_fechas, formulario_servicio, mostrar_orden_admin

# Columnas por las que se puede ordenar el historial: texto en pantalla -> campo del registro
COLUMNAS_ORDEN = {
    "N° de orden (más reciente)": "id",
    "Comensales": "comensales",
    "Costo por plato": "costo_por_plato",
    "Merma física (envases)": "merma_fisica_envases",
    "Pérdida por merma": "perdida_merma",
    "Valor de venta por plato": "precio_venta_plato",
    "Ingreso total": "ingreso_total",
    "Costo total": "costo_total",
}

METODO_EXTERNO = "Externo (merge por bloques)"


def _cargar_datos(repo, forzar=False):
    """
    Trae órdenes y detalle desde Supabase y los deja en la sesión para no
    consultar la base en cada clic. El botón "Actualizar" fuerza una nueva lectura.
    """
    if forzar or "datos_admin" not in st.session_state:
        st.session_state["datos_admin"] = (repo.obtener_ordenes(), repo.obtener_detalle_ordenes())
    return st.session_state["datos_admin"]


def _barras(df, x, y, titulo, y_titulo="Pérdida ($)"):
    """Gráfico de barras horizontales ordenado de mayor a menor valor."""
    grafico = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y(f"{x}:N", sort="-x", title=None),
            x=alt.X(f"{y}:Q", title=y_titulo),
            tooltip=[x, alt.Tooltip(f"{y}:Q", format=",.2f")],
        )
        .properties(title=titulo, height=max(160, 34 * len(df)))
    )
    st.altair_chart(grafico)


# ---------------------------------------------------------------------
# Panel principal (3 pestañas)
# ---------------------------------------------------------------------

def pagina_panel(repo, usuario, recetas):
    exigir_costos(usuario)
    st.header("Panel gerencial")

    if st.button("🔄 Actualizar datos"):
        _cargar_datos(repo, forzar=True)
    ordenes, detalle = _cargar_datos(repo)

    if not ordenes:
        st.info("Aún no hay órdenes registradas. Ingresa servicios desde «Nueva orden» para ver el panel.")
        return

    tab_resumen, tab_historial, tab_mermas = st.tabs(
        ["📊 Resumen ejecutivo", "📋 Historial de preparaciones", "🗑️ Análisis de mermas"]
    )
    with tab_resumen:
        _tab_resumen(ordenes)
    with tab_historial:
        _tab_historial(ordenes, detalle, recetas)
    with tab_mermas:
        _tab_mermas(ordenes, detalle, recetas)


# ---------------------------------------------------------------------
# Pestaña 1: resumen ejecutivo
# ---------------------------------------------------------------------

def _tab_resumen(ordenes):
    k = calcular_kpis(ordenes)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Servicios realizados", k["servicios"])
    c2.metric("Costo total acumulado", formato_clp(k["costo_total"]))
    c3.metric("Pérdida total por merma", formato_clp(k["perdida_merma"]))
    c4.metric("Ingresos proyectados por venta", formato_clp(k["ingresos"]))

    c5, c6, c7 = st.columns(3)
    c5.metric("Utilidad proyectada", formato_clp(k["utilidad"]))
    c6.metric("Merma sobre el costo", f"{k['pct_merma']:.1f} %")
    c7.metric("Comensales atendidos", k["comensales"])

    st.subheader("Las 5 órdenes con mayor pérdida por merma")
    top = top_ordenes_por_perdida(ordenes, 5)       # sale de la cola con prioridad
    tabla = pd.DataFrame({
        "N° orden": [o["id"] for o in top],
        "Menú": [o["menu"] for o in top],
        "Comensales": [o["comensales"] for o in top],
        "Pérdida por merma ($)": [o["perdida_merma"] for o in top],
        "Costo total ($)": [o["costo_total"] for o in top],
    })
    st.dataframe(tabla, hide_index=True, column_config={
        "Pérdida por merma ($)": st.column_config.NumberColumn(format="$%.0f"),
        "Costo total ($)": st.column_config.NumberColumn(format="$%.0f"),
    })


# ---------------------------------------------------------------------
# Pestaña 2: historial filtrable
# ---------------------------------------------------------------------

def _tab_historial(ordenes, detalle, recetas):
    st.subheader("Historial completo de órdenes")

    f1, f2 = st.columns(2)
    menus = ["Todos"] + sorted({o["menu"] for o in ordenes})
    menu = f1.selectbox("Filtrar por tipo de menú", menus)
    columna_txt = f2.selectbox("Ordenar por", list(COLUMNAS_ORDEN))

    f3, f4 = st.columns(2)
    sentido = f3.radio("Sentido", ["Mayor a menor", "Menor a mayor"], horizontal=True)
    metodo = f4.selectbox("Método de ordenamiento", list(ALGORITMOS_INTERNOS) + [METODO_EXTERNO])

    tam_bloque = TAM_BLOQUE_EXTERNO
    if metodo == METODO_EXTERNO:
        tam_bloque = int(st.number_input("Tamaño de bloque (registros en memoria)", min_value=1,
                                         value=TAM_BLOQUE_EXTERNO, step=10))

    filtradas = filtrar_por_menu(ordenes, menu)                    # búsqueda secuencial
    if metodo == "Burbuja" and len(filtradas) > 1500:
        st.warning("Burbuja es lenta con muchos registros (O(n²)). Considera Merge sort o Quicksort.")
    ordenadas, descripcion = ordenar_historial(
        filtradas, COLUMNAS_ORDEN[columna_txt], sentido == "Mayor a menor", metodo, tam_bloque
    )

    if not ordenadas:
        st.info("No hay órdenes para ese filtro.")
        return

    df = pd.DataFrame({
        "N° orden": [o["id"] for o in ordenadas],
        "Fecha": formatear_fechas(pd.Series([o["fecha"] for o in ordenadas])),
        "Menú": [o["menu"] for o in ordenadas],
        "Comensales": [o["comensales"] for o in ordenadas],
        "Costo por plato ($)": [o["costo_por_plato"] for o in ordenadas],
        "Merma física (envases)": [o["merma_fisica_envases"] for o in ordenadas],
        "Pérdida por merma ($)": [o["perdida_merma"] for o in ordenadas],
        "Valor de venta por plato ($)": [o["precio_venta_plato"] for o in ordenadas],
        "Costo total ($)": [o["costo_total"] for o in ordenadas],
        "Ingreso total ($)": [o["ingreso_total"] for o in ordenadas],
    })
    st.dataframe(df, hide_index=True, column_config={
        "Costo por plato ($)": st.column_config.NumberColumn(format="$%.2f"),
        "Merma física (envases)": st.column_config.NumberColumn(format="%.2f"),
        "Pérdida por merma ($)": st.column_config.NumberColumn(format="$%.2f"),
        "Valor de venta por plato ($)": st.column_config.NumberColumn(format="$%.2f"),
        "Costo total ($)": st.column_config.NumberColumn(format="$%.0f"),
        "Ingreso total ($)": st.column_config.NumberColumn(format="$%.2f"),
    })
    st.caption(f"{len(ordenadas)} orden(es) · {descripcion}")

    # Detalle por ingrediente de una orden elegida
    with st.expander("Ver desglose de insumos de una orden"):
        elegida = st.selectbox("N° de orden", [o["id"] for o in ordenadas], key="detalle_orden")
        lineas = filtrar_secuencial(detalle, lambda d: d["orden_id"] == elegida)
        det = pd.DataFrame({
            "Ingrediente": [d["ingrediente"] for d in lineas],
            "Cantidad a preparar": [texto_cantidad_receta(d["cantidad_preparar"], d["unidad_receta"]) for d in lineas],
            "Cantidad requerida": [texto_envases(d["envases_requeridos"], d["unidad_compra"]) for d in lineas],
            "Costo envases ($)": [d["costo_envases"] for d in lineas],
            "Merma (envase)": [d["merma_envases"] for d in lineas],
            "Pérdida ($)": [d["perdida_merma"] for d in lineas],
        })
        st.dataframe(det, hide_index=True)


# ---------------------------------------------------------------------
# Pestaña 3: análisis de mermas
# ---------------------------------------------------------------------

def _tab_mermas(ordenes, detalle, recetas):
    por_menu = resumen_por_menu(ordenes)
    por_ing = resumen_por_ingrediente(detalle)

    # ---- Decisiones logísticas: lo más importante primero ----
    menus_ord, _ = ordenar(por_menu, lambda f: f["perdida_merma"], True, "Merge sort")   # mayor pérdida primero
    peor_menu = menus_ord[0]
    ranking_ing = ranking_jerarquico(por_ing, "ingrediente", "perdida_merma")
    st.info(
        f"**Menú que más pérdida acumula:** {peor_menu['menu']} ({formato_clp(peor_menu['perdida_merma'])}, "
        f"{peor_menu['pct_merma']:.1f} % de su costo).  \n"
        f"**Ingrediente que más pérdida genera:** {ranking_ing[0][1]} ({formato_clp(ranking_ing[0][2])})."
    )

    st.subheader("Pérdida por merma según menú")
    dfm = pd.DataFrame(menus_ord)
    _barras(dfm.rename(columns={"menu": "Menú", "perdida_merma": "Pérdida ($)"}), "Menú", "Pérdida ($)",
            "Pérdida acumulada por menú")
    st.dataframe(
        dfm.rename(columns={"menu": "Menú", "servicios": "Servicios", "comensales": "Comensales",
                            "costo_total": "Costo total ($)", "perdida_merma": "Pérdida por merma ($)",
                            "ingreso_total": "Ingreso total ($)", "pct_merma": "% merma sobre costo"}),
        hide_index=True,
        column_config={
            "Costo total ($)": st.column_config.NumberColumn(format="$%.0f"),
            "Pérdida por merma ($)": st.column_config.NumberColumn(format="$%.0f"),
            "Ingreso total ($)": st.column_config.NumberColumn(format="$%.0f"),
            "% merma sobre costo": st.column_config.NumberColumn(format="%.1f %%"),
        },
    )

    st.subheader("Pérdida y consumo según ingrediente")
    st.caption("Ranking construido con un árbol binario de búsqueda (recorrido inorden inverso).")
    por_nombre = {f["ingrediente"]: f for f in por_ing}
    filas = []
    for pos, nombre, _valor in ranking_ing:
        f = por_nombre[nombre]
        filas.append({"Puesto": pos, "Ingrediente": nombre, "Envases consumidos": f["envases"],
                      "Costo ($)": f["costo_envases"], "Merma (envases)": f["merma_envases"],
                      "Pérdida por merma ($)": f["perdida_merma"], "% merma sobre costo": f["pct_merma"]})
    dfi = pd.DataFrame(filas)
    _barras(dfi.rename(columns={"Pérdida por merma ($)": "Pérdida ($)"}), "Ingrediente", "Pérdida ($)",
            "Pérdida acumulada por ingrediente")
    st.dataframe(dfi, hide_index=True, column_config={
        "Costo ($)": st.column_config.NumberColumn(format="$%.0f"),
        "Pérdida por merma ($)": st.column_config.NumberColumn(format="$%.0f"),
        "% merma sobre costo": st.column_config.NumberColumn(format="%.1f %%"),
    })

    with st.expander("🔗 Menús que comparten ingredientes (grafo menú–ingrediente)"):
        st.caption("Si dos menús comparten un ingrediente, preparar ambos en el mismo turno "
                   "permitiría aprovechar mejor los envases abiertos y reducir la merma.")
        grafo = construir_grafo(recetas)
        elegido = st.selectbox("Menú", [r.nombre for r in recetas], key="grafo_menu")
        st.write("**Ingredientes:** " + ", ".join(grafo.vecinos(elegido)))
        relacionados = menus_relacionados(grafo, elegido)
        if relacionados:
            st.dataframe(pd.DataFrame({
                "Menú relacionado": [m for m, _ in relacionados],
                "Ingredientes en común": [", ".join(c) for _, c in relacionados],
            }), hide_index=True)


# ---------------------------------------------------------------------
# Nueva orden con vista completa (administrador)
# ---------------------------------------------------------------------

def pagina_nueva_orden(repo, usuario, recetas):
    """Mismo formulario de cocina, pero mostrando también los costos y la merma."""
    exigir_costos(usuario)
    st.header("Nueva orden (vista completa)")

    solicitud = formulario_servicio(recetas, "admin")
    if solicitud is False:
        st.session_state.pop("ultima_orden_admin", None)
    elif solicitud is not None:
        receta, comensales = solicitud
        try:
            orden_id, resultado = registrar_orden(repo, usuario, receta, comensales)
        except ErrorBaseDatos as e:
            st.error(str(e))
            return
        st.session_state["ultima_orden_admin"] = (orden_id, resultado)
        st.session_state.pop("datos_admin", None)      # fuerza a releer el panel con la orden nueva

    ultima = st.session_state.get("ultima_orden_admin")
    if ultima is not None:
        mostrar_orden_admin(*ultima)
