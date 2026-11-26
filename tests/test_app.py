# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Evaluación N°3 - 26 de noviembre de 2026
# Archivo  : tests/test_app.py
# ---------------------------------------------------------------------
# Prueba la aplicación Streamlit completa (login, cocina, administrador)
# con el framework de pruebas de Streamlit (AppTest) y una base falsa en
# memoria. Verifica sobre todo que COCINA NUNCA VE dinero ni mermas.
# =====================================================================

import os
import re

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from src import base_datos
from tests.fakes import ClienteFalso

RUTA_APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
PALABRAS_PROHIBIDAS_COCINA = ["costo", "merma", "pérdida", "perdida", "venta", "ingreso", "utilidad", "$"]


@pytest.fixture
def cliente(monkeypatch):
    """Cada prueba arranca con una base nueva y la app usando el cliente falso."""
    falso = ClienteFalso()
    monkeypatch.setattr(base_datos, "crear_cliente_supabase", lambda: falso)
    st.cache_resource.clear()
    return falso


def nueva_app():
    at = AppTest.from_file(RUTA_APP, default_timeout=30)
    at.run()
    return at


def ingresar(at, usuario, clave):
    at.text_input[0].set_value(usuario)
    at.text_input[1].set_value(clave)
    at.button[0].click().run()
    return at


def todo_el_texto(at):
    """Junta todo el texto visible de la pantalla (títulos, métricas, tablas, avisos...)."""
    partes = []
    for grupo in (at.title, at.header, at.subheader, at.markdown, at.caption, at.text, at.info,
                  at.success, at.warning, at.error):
        partes += [e.value for e in grupo]
    for m in at.metric:
        partes += [m.label, str(m.value)]
    for d in at.dataframe:
        partes.append(" ".join(map(str, d.value.columns)))
        partes.append(d.value.to_csv())
    return "\n".join(partes).lower()


def enviar_formulario(at, menu, comensales):
    if menu is not None:
        at.selectbox[0].select(menu)
    at.number_input[0].set_value(comensales)
    at.button[0].click().run()     # primer botón de la página principal = enviar del formulario
    return at


# ---------------- Login ----------------

def test_login_muestra_formulario(cliente):
    at = nueva_app()
    assert not at.exception
    assert any("Control de Alimentos" in t.value for t in at.title)
    assert len(at.text_input) == 2


def test_login_incorrecto(cliente):
    at = nueva_app()
    ingresar(at, "cocina", "mala")
    assert any("incorrectos" in e.value for e in at.error)
    assert "usuario" not in at.session_state


def test_bloqueo_tras_5_intentos(cliente):
    at = nueva_app()
    for _ in range(5):
        ingresar(at, "cocina", "mala")
    ingresar(at, "cocina", "Cocina2026!")                          # aunque ahora sea la clave correcta
    assert any("Espere" in e.value for e in at.error)
    assert "usuario" not in at.session_state


# ---------------- Perfil cocina ----------------

def test_cocina_flujo_completo_y_no_ve_dinero(cliente):
    at = nueva_app()
    ingresar(at, "cocina", "Cocina2026!")
    assert not at.exception
    assert at.session_state["usuario"].rol == "cocina"
    assert list(at.sidebar.radio[0].options) == ["🍽️ Nueva orden", "📜 Historial"]

    enviar_formulario(at, "Arroz con Pollo y Ensalada", 4)
    assert not at.exception
    assert any("Orden N°1 registrada" in s.value for s in at.success)

    # Quedó guardada en la base con todos sus cálculos
    assert len(cliente.tablas["ordenes"]) == 1 and len(cliente.tablas["detalle_orden"]) == 4
    assert cliente.tablas["ordenes"][0]["perdida_merma"] == 2100.0

    # La pantalla muestra cantidades...
    texto = todo_el_texto(at)
    assert "trutro de pollo" in texto and "4 unidades" in texto and "1 paquete" in texto and "1 litro" in texto
    # ...y NADA de plata ni mermas
    for palabra in PALABRAS_PROHIBIDAS_COCINA:
        assert palabra not in texto, f"cocina ve '{palabra}'"
    assert not any(re.search(r"\d{4}", str(d.value.to_csv())) for d in at.dataframe)   # ningún monto de 4+ dígitos


@pytest.mark.parametrize("comensales,mensaje", [(0, "cero"), (-4, "negativa"), (None, "vacío")])
def test_cocina_validaciones(cliente, comensales, mensaje):
    at = nueva_app()
    ingresar(at, "cocina", "Cocina2026!")
    at.selectbox[0].select("Charquicán Simple")
    at.number_input[0].set_value(comensales)
    at.button[0].click().run()
    assert any(mensaje in e.value for e in at.error)
    assert cliente.tablas["ordenes"] == []


def test_cocina_sin_menu(cliente):
    at = nueva_app()
    ingresar(at, "cocina", "Cocina2026!")
    at.number_input[0].set_value(5)
    at.button[0].click().run()
    assert any("menú" in e.value.lower() for e in at.error)
    assert cliente.tablas["ordenes"] == []


def test_cocina_rechaza_decimales(cliente):
    at = nueva_app()
    ingresar(at, "cocina", "Cocina2026!")
    at.selectbox[0].select("Charquicán Simple")
    at.number_input[0].set_value(2.5)
    at.button[0].click().run()
    assert any("entero" in e.value for e in at.error)
    assert cliente.tablas["ordenes"] == []


def test_cocina_varias_ordenes_y_pila(cliente):
    at = nueva_app()
    ingresar(at, "cocina", "Cocina2026!")
    enviar_formulario(at, "Charquicán Simple", 8)
    enviar_formulario(at, "Fideos con Huevo y Tomate", 12)
    assert len(cliente.tablas["ordenes"]) == 2
    pila = at.session_state["pila_ordenes"]
    assert [p["orden"] for p in pila] == [2, 1]                   # la más reciente primero (LIFO)


def test_cocina_historial_sin_dinero(cliente):
    at = nueva_app()
    ingresar(at, "cocina", "Cocina2026!")
    enviar_formulario(at, "Tortilla de Papas y Cebolla", 10)
    at.sidebar.radio[0].set_value("📜 Historial").run()
    assert not at.exception
    texto = todo_el_texto(at)
    assert "tortilla de papas y cebolla" in texto
    for palabra in PALABRAS_PROHIBIDAS_COCINA:
        assert palabra not in texto, f"historial de cocina muestra '{palabra}'"
    at.selectbox[0].select(1).run()
    assert not at.exception
    for palabra in PALABRAS_PROHIBIDAS_COCINA:
        assert palabra not in todo_el_texto(at)


def test_cocina_no_puede_abrir_pantallas_de_admin(cliente):
    at = nueva_app()
    ingresar(at, "cocina", "Cocina2026!")
    opciones = at.sidebar.radio[0].options
    assert all("Panel" not in o for o in opciones)
    # aunque se intentara llamar directo, el guardia corta con PermissionError
    from src.vistas import admin
    with pytest.raises(PermissionError):
        admin.pagina_panel(None, at.session_state["usuario"], [])


def test_error_de_bd_al_guardar_se_muestra(cliente):
    at = nueva_app()
    ingresar(at, "cocina", "Cocina2026!")
    cliente.falla_detalle = True
    enviar_formulario(at, "Charquicán Simple", 8)
    assert any("No se pudo guardar" in e.value for e in at.error)
    assert cliente.tablas["ordenes"] == []


# ---------------- Perfil administrador ----------------

def llenar_ordenes_como_admin(at):
    at.sidebar.radio[0].set_value("🍽️ Nueva orden").run()
    for menu, n in [("Arroz con Pollo y Ensalada", 4), ("Tortilla de Papas y Cebolla", 4),
                    ("Arroz con Pollo y Ensalada", 11), ("Papas Cocidas con Huevo y Lechuga", 25)]:
        enviar_formulario(at, menu, n)
        assert not at.exception


def test_admin_ve_todo_en_nueva_orden(cliente):
    at = nueva_app()
    ingresar(at, "admin", "Admin2026!")
    assert at.session_state["usuario"].ve_costos
    assert "📊 Panel gerencial" in at.sidebar.radio[0].options
    at.sidebar.radio[0].set_value("🍽️ Nueva orden").run()
    enviar_formulario(at, "Arroz con Pollo y Ensalada", 4)
    assert not at.exception
    etiquetas = {m.label: m.value for m in at.metric}
    assert etiquetas["Costo total"] == "$8.300"
    assert etiquetas["Costo por plato"] == "$2.075,00"
    assert etiquetas["Valor de venta por plato"] == "$2.593,75"
    assert etiquetas["Pérdida por merma"] == "$2.100"
    assert etiquetas["Ingreso proyectado"] == "$10.375"


def test_admin_panel_vacio(cliente):
    at = nueva_app()
    ingresar(at, "admin", "Admin2026!")
    assert not at.exception
    assert any("Aún no hay órdenes" in i.value for i in at.info)


def test_admin_panel_con_datos(cliente):
    at = nueva_app()
    ingresar(at, "admin", "Admin2026!")
    llenar_ordenes_como_admin(at)
    at.sidebar.radio[0].set_value("📊 Panel gerencial").run()
    assert not at.exception, at.exception

    # --- KPIs ---
    kpis = {m.label: m.value for m in at.metric}
    assert kpis["Servicios realizados"] == "4"
    ordenes = cliente.tablas["ordenes"]
    costo = sum(o["costo_total"] for o in ordenes)
    assert kpis["Costo total acumulado"] == "$" + f"{costo:,.0f}".replace(",", ".")
    perdida = sum(o["perdida_merma"] for o in ordenes)
    assert kpis["Pérdida total por merma"] == "$" + f"{perdida:,.0f}".replace(",", ".")
    ingresos = costo * 1.25
    assert kpis["Ingresos proyectados por venta"] == "$" + f"{ingresos:,.0f}".replace(",", ".")

    # --- Pestañas ---
    assert len(at.tabs) == 3
    # --- Historial: filtro + orden + método ---
    assert len(at.dataframe) >= 2
    historial_df = [d.value for d in at.dataframe if "Valor de venta por plato ($)" in d.value.columns][0]
    assert len(historial_df) == 4
    assert set(historial_df.columns) >= {"Comensales", "Costo por plato ($)", "Merma física (envases)",
                                         "Pérdida por merma ($)", "Valor de venta por plato ($)"}


def test_admin_filtro_por_menu_y_ordenamientos(cliente):
    at = nueva_app()
    ingresar(at, "admin", "Admin2026!")
    llenar_ordenes_como_admin(at)
    at.sidebar.radio[0].set_value("📊 Panel gerencial").run()

    sb = {s.label: s for s in at.selectbox}
    sb["Filtrar por tipo de menú"].select("Arroz con Pollo y Ensalada").run()
    assert not at.exception
    df = [d.value for d in at.dataframe if "Valor de venta por plato ($)" in d.value.columns][0]
    assert list(df["Menú"].unique()) == ["Arroz con Pollo y Ensalada"] and len(df) == 2

    for metodo in ["Quicksort", "Inserción", "Burbuja", "Externo (merge por bloques)", "Merge sort"]:
        sb = {s.label: s for s in at.selectbox}
        sb["Método de ordenamiento"].select(metodo).run()
        assert not at.exception, metodo
        df = [d.value for d in at.dataframe if "Valor de venta por plato ($)" in d.value.columns][0]
        assert len(df) == 2
        sb = {s.label: s for s in at.selectbox}
        sb["Ordenar por"].select("Pérdida por merma").run()
        df = [d.value for d in at.dataframe if "Valor de venta por plato ($)" in d.value.columns][0]
        valores = list(df["Pérdida por merma ($)"])
        assert valores == sorted(valores, reverse=True)           # por defecto: mayor a menor


def test_admin_mermas_menus_y_ingredientes(cliente):
    at = nueva_app()
    ingresar(at, "admin", "Admin2026!")
    llenar_ordenes_como_admin(at)
    at.sidebar.radio[0].set_value("📊 Panel gerencial").run()
    texto = todo_el_texto(at)
    assert "menú que más pérdida acumula" in texto
    assert "ingrediente que más pérdida genera" in texto
    cols = [set(d.value.columns) for d in at.dataframe]
    assert any("Pérdida por merma ($)" in c and "Envases consumidos" in c for c in cols)    # tabla por ingrediente
    assert any("% merma sobre costo" in c and "Servicios" in c for c in cols)               # tabla por menú


def test_cerrar_sesion_vuelve_al_login(cliente):
    at = nueva_app()
    ingresar(at, "admin", "Admin2026!")
    assert "usuario" in at.session_state
    at.sidebar.button[0].click().run()
    assert "usuario" not in at.session_state
    assert len(at.text_input) == 2


# ---------------- Configuración / base vacía ----------------

def test_sin_credenciales_muestra_instrucciones(monkeypatch):
    def sin_credenciales():
        from src.config import ConfiguracionError
        raise ConfiguracionError("No encontré las credenciales de Supabase.")
    monkeypatch.setattr(base_datos, "crear_cliente_supabase", sin_credenciales)
    st.cache_resource.clear()
    at = nueva_app()
    assert any("credenciales" in e.value for e in at.error)
    assert not at.exception


def test_base_sin_datos_avisa(monkeypatch):
    vacio = ClienteFalso(con_datos=False)
    monkeypatch.setattr(base_datos, "crear_cliente_supabase", lambda: vacio)
    st.cache_resource.clear()
    at = nueva_app()
    assert any("incompleta" in e.value for e in at.error)
