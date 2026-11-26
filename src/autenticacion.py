# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/autenticacion.py
# Librerías: hashlib, hmac, os (estándar); busqueda.py y modelos.py (propios)
# ---------------------------------------------------------------------
# Identificación de usuarios y control de roles (Actividad 1 y 3).
#   - Las contraseñas NO se guardan en texto plano: se guarda un hash PBKDF2
#     con sal aleatoria (formato "pbkdf2_sha256$iteraciones$sal$hash").
#   - El usuario se busca con búsqueda secuencial en la lista de usuarios.
#   - Los permisos (ve_costos, registra_ordenes) salen de la tabla 'roles'.
# =====================================================================

import hashlib
import hmac
import os

from src.busqueda import buscar_por_texto
from src.modelos import Usuario

ROL_COCINA = "cocina"
ROL_ADMIN = "administrador"

ITERACIONES = 120_000      # cuántas vueltas hace PBKDF2: más vueltas = más difícil de adivinar por fuerza bruta


def hashear_password(password, sal=None, iteraciones=ITERACIONES):
    """
    Devuelve el hash de la contraseña en formato texto para guardarlo en la BD.
    Si no se entrega sal, se genera una aleatoria de 16 bytes.
    """
    if sal is None:
        sal = os.urandom(16)
    derivado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, iteraciones)
    return f"pbkdf2_sha256${iteraciones}${sal.hex()}${derivado.hex()}"


def verificar_password(password, almacenado):
    """True si la contraseña coincide con el hash guardado. Nunca lanza error por un hash mal formado."""
    try:
        algoritmo, iteraciones, sal_hex, hash_hex = almacenado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        derivado = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(sal_hex), int(iteraciones)
        )
        # compare_digest compara en tiempo constante (evita ataques por tiempos de respuesta)
        return hmac.compare_digest(derivado.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def autenticar(filas_usuarios, filas_roles, username, password):
    """
    Valida el acceso. Pasos:
      1. Busco el usuario por su nombre con búsqueda secuencial.
      2. Verifico que esté activo.
      3. Comparo la contraseña con el hash guardado.
      4. Busco su rol (también secuencial) para armar los permisos.
    Devuelve un Usuario o None. El mensaje de error es siempre el mismo
    ("usuario o contraseña incorrectos") para no revelar si el usuario existe.
    """
    if not username or not password:
        return None

    fila = buscar_por_texto(filas_usuarios, lambda f: f["username"], username)
    if fila is None or not fila.get("activo", True):
        return None
    if not verificar_password(password, fila["password_hash"]):
        return None

    rol = buscar_por_texto(filas_roles, lambda r: r["rol"], fila["rol"])
    if rol is None:                         # usuario con un rol que no existe: no se le da acceso
        return None

    return Usuario(
        id=int(fila["id"]),
        username=fila["username"],
        nombre_completo=fila["nombre_completo"],
        rol=fila["rol"],
        ve_costos=bool(rol["ve_costos"]),
        registra_ordenes=bool(rol["registra_ordenes"]),
    )


def exigir_costos(usuario):
    """
    Guardia para las pantallas gerenciales: si el usuario no puede ver costos
    se corta con PermissionError. Es una segunda barrera por si la navegación falla.
    """
    if usuario is None or not usuario.ve_costos:
        raise PermissionError("Este perfil no tiene acceso a información financiera.")
