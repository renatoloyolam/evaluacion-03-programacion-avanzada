# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/config.py
# Librerías: os (estándar), fractions (estándar), streamlit (solo para leer st.secrets)
# ---------------------------------------------------------------------
# Acá van las constantes del negocio y la lectura de credenciales.
# Dejé todo lo "ajustable" en este archivo para no andar buscando
# números sueltos por el código si el profesor cambia algún supuesto.
# =====================================================================

import os
from fractions import Fraction


class ConfiguracionError(Exception):
    """Se lanza cuando faltan las credenciales de Supabase."""


# ---------------------------------------------------------------------
# Constantes del negocio
# ---------------------------------------------------------------------

# Ganancia pedida en el enunciado (25 %). Uso Fraction y no float para
# que 1.25 * costo no arrastre errores de decimales binarios.
MARGEN_GANANCIA = Fraction(25, 100)

# "sobre_costo": precio = costo * (1 + 25 %)      <- interpretación por defecto
# "sobre_venta": precio = costo / (1 - 25 %)      <- el 25 % es margen sobre el precio
# El enunciado dice "asumiendo una ganancia del 25%" y no aclara la base,
# así que dejo la más habitual (sobre el costo) y la otra queda a un cambio.
BASE_MARGEN = "sobre_costo"

# Cómo se calcula cuánto hay que comprar de cada ingrediente:
# "comensales": envases = ceil(comensales / personas_por_envase)
#     -> usa la columna "Utilidad" de la tabla tal cual (X personas por paquete).
# "receta": envases = ceil(cantidad_de_la_receta_escalada / personas_por_envase)
#     -> trata las unidades/porciones de la receta como la demanda real.
# Por defecto uso "comensales" porque la tabla de utilidad está expresada en personas.
MODO_DEMANDA = "comensales"

# Tope razonable de comensales por servicio (evita que alguien escriba 9999999).
MAX_COMENSALES = 5000

# Tamaño de bloque del ordenamiento externo (cuántos registros caben "en memoria").
TAM_BLOQUE_EXTERNO = 50


# ---------------------------------------------------------------------
# Credenciales de Supabase
# ---------------------------------------------------------------------

def obtener_credenciales_supabase():
    """
    Devuelve (url, key) de Supabase.

    Primero intenta con st.secrets (archivo .streamlit/secrets.toml, que NO se
    sube a GitHub gracias al .gitignore). Si no está, prueba con variables de
    entorno SUPABASE_URL y SUPABASE_KEY. Así las claves nunca quedan escritas
    en el código fuente.
    """
    url = None
    key = None

    # Intento 1: st.secrets. Se importa acá adentro para que los módulos de
    # cálculo y los tests funcionen aunque Streamlit no esté instalado.
    try:
        import streamlit as st
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except Exception:
        # No hay secrets.toml o le falta la sección [supabase]; probamos el entorno.
        pass

    # Intento 2: variables de entorno
    if not url:
        url = os.environ.get("SUPABASE_URL")
    if not key:
        key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise ConfiguracionError(
            "No encontré las credenciales de Supabase. Crea el archivo "
            ".streamlit/secrets.toml con la sección [supabase] (url y key), "
            "o define las variables de entorno SUPABASE_URL y SUPABASE_KEY."
        )
    return url, key
