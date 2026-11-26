# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/vistas/login.py
# Librerías: streamlit, time (estándar); autenticacion (propio)
# ---------------------------------------------------------------------
# Pantalla de ingreso. La sesión se mantiene en st.session_state["usuario"];
# mientras ese valor sea None, app.py no deja pasar a ninguna otra pantalla.
# =====================================================================

import time

import streamlit as st

from src.autenticacion import autenticar

MAX_INTENTOS = 5          # intentos fallidos antes de bloquear
SEGUNDOS_BLOQUEO = 30     # cuánto dura el bloqueo


def mostrar_login(repo):
    st.title("🍲 Control de Alimentos y Mermas")
    st.caption("Academia Politécnica Militar · Programación Avanzada · Evaluación N°3")

    # Anti fuerza bruta simple: si ya falló muchas veces, se bloquea un rato
    bloqueado_hasta = st.session_state.get("bloqueado_hasta", 0)
    restante = int(bloqueado_hasta - time.time())
    if restante > 0:
        st.error(f"Demasiados intentos fallidos. Espere {restante} segundos e intente de nuevo.")
        return

    with st.form("form_login"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        entrar = st.form_submit_button("Ingresar", type="primary")

    if not entrar:
        return

    usuario = autenticar(repo.obtener_usuarios(), repo.obtener_roles(), username, password)
    if usuario is None:
        st.session_state["intentos"] = st.session_state.get("intentos", 0) + 1
        if st.session_state["intentos"] >= MAX_INTENTOS:
            st.session_state["bloqueado_hasta"] = time.time() + SEGUNDOS_BLOQUEO
            st.session_state["intentos"] = 0
        # Mismo mensaje se haya equivocado el usuario o la clave (no se revela cuál)
        st.error("Usuario o contraseña incorrectos.")
        return

    st.session_state["intentos"] = 0
    st.session_state["usuario"] = usuario
    st.rerun()
