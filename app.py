# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : app.py  (punto de entrada)
# Ejecutar : streamlit run app.py
# Librerías: streamlit, pandas, altair, supabase (ver requirements.txt)
# ---------------------------------------------------------------------
# Sistema de control de alimentos, mermas y costos del casino.
#   - Perfil COCINA: ingresa menú + comensales y recibe la orden de
#     preparación (solo cantidades). No ve costos ni mermas.
#   - Perfil ADMINISTRADOR: panel gerencial con KPIs, historial filtrable
#     y análisis de mermas, además de poder registrar órdenes.
#
# Organización del proyecto (cada archivo hace una sola cosa):
#   app.py               -> login, navegación entre roles (este archivo)
#   src/config.py        -> constantes y lectura de credenciales (st.secrets)
#   src/modelos.py       -> clases Ingrediente, Receta, Usuario, resultados
#   src/estructuras.py   -> TDAs: lista, pila, cola, cola con prioridad, árbol, grafo
#   src/calculo.py       -> motor de cálculo (indivisibilidad, merma, costos, precio)
#   src/ordenamiento.py  -> ordenamiento interno y externo
#   src/busqueda.py      -> búsqueda secuencial
#   src/autenticacion.py -> hash de claves, validación de acceso y roles
#   src/base_datos.py    -> todas las consultas a Supabase
#   src/analisis.py      -> KPIs, resúmenes y rankings del panel gerencial
#   src/servicios.py     -> une cálculo + guardado
#   src/vistas/          -> pantallas (login, cocina, administrador)
# =====================================================================

import streamlit as st

from src import base_datos
from src.autenticacion import ROL_ADMIN, ROL_COCINA
from src.config import ConfiguracionError
from src.vistas import admin, cocina
from src.vistas.login import mostrar_login

st.set_page_config(page_title="Control de Alimentos y Mermas", page_icon="🍲", layout="wide")


@st.cache_resource
def obtener_repositorio():
    """
    Crea el repositorio una sola vez (el cliente de Supabase se reutiliza entre
    recargas y usuarios). Se llama a través del módulo base_datos para que los
    tests puedan reemplazarlo por uno falso.
    """
    return base_datos.RepositorioSupabase(base_datos.crear_cliente_supabase())


def preparar_repositorio():
    """
    Obtiene el repositorio y comprueba que la base esté lista. Si algo falla
    muestra qué hacer en pantalla y detiene la app (st.stop), en vez de dejar
    un error técnico.
    """
    try:
        repo = obtener_repositorio()
    except ConfiguracionError as e:
        st.error(str(e))
        st.code('[supabase]\nurl = "https://TU-PROYECTO.supabase.co"\nkey = "sb_secret_..."', language="toml")
        st.stop()
    except Exception as e:
        st.error(f"No se pudo crear el cliente de Supabase: {e}")
        st.stop()

    # Diagnóstico una sola vez por sesión (3 consultas livianas)
    if "diagnostico_ok" not in st.session_state:
        try:
            cantidades = repo.contar_registros_base()
        except Exception as e:
            st.error(
                "No se pudo leer la base de datos. Revisa que ejecutaste sql/01_esquema.sql y que "
                "en secrets.toml usas la clave SECRETA (sb_secret_...) y no la publishable.\n\n"
                f"Detalle técnico: {e}"
            )
            st.stop()
        if cantidades["ingredientes"] < 10 or cantidades["recetas"] < 10 or cantidades["usuarios"] < 1:
            st.error(
                f"La base está incompleta (ingredientes: {cantidades['ingredientes']}, recetas: "
                f"{cantidades['recetas']}, usuarios: {cantidades['usuarios']}). Ejecuta sql/02_datos_iniciales.sql. "
                "Si ya lo hiciste y sigue en 0, probablemente estás usando la clave publishable en vez de la secreta."
            )
            st.stop()
        st.session_state["diagnostico_ok"] = True
    return repo


def cerrar_sesion():
    """Borra todo el estado de la sesión (usuario, catálogo, datos del panel) y vuelve al login."""
    for clave in list(st.session_state.keys()):
        del st.session_state[clave]


# Páginas disponibles por rol: texto del menú -> función que la dibuja.
# El rol se lee de la base de datos (tabla usuarios), nunca de lo que escriba el usuario.
PAGINAS = {
    ROL_COCINA: {
        "🍽️ Nueva orden": cocina.pagina_nueva_orden,
        "📜 Historial": cocina.pagina_historial,
    },
    ROL_ADMIN: {
        "📊 Panel gerencial": admin.pagina_panel,
        "🍽️ Nueva orden": admin.pagina_nueva_orden,
    },
}


def main():
    repo = preparar_repositorio()

    # Sin sesión iniciada solo se muestra el login
    usuario = st.session_state.get("usuario")
    if usuario is None:
        mostrar_login(repo)
        return

    # Catálogo de recetas: se carga una vez por sesión
    if "recetas" not in st.session_state:
        st.session_state["recetas"] = repo.obtener_recetas()
    recetas = st.session_state["recetas"]

    # Barra lateral: quién está conectado, menú según su rol y botón para salir
    paginas = PAGINAS.get(usuario.rol)
    if paginas is None:
        st.error("Su perfil no tiene pantallas asignadas.")
        cerrar_sesion()
        return

    with st.sidebar:
        st.markdown(f"### 👤 {usuario.nombre_completo}")
        st.caption(f"Perfil: **{usuario.rol}**")
        seleccion = st.radio("Navegación", list(paginas), label_visibility="collapsed")
        st.divider()
        if st.button("Cerrar sesión"):
            cerrar_sesion()
            st.rerun()

    paginas[seleccion](repo, usuario, recetas)


main()
