# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Evaluación N°3 - 26 de noviembre de 2026
# Archivo  : scripts/generar_hash.py
# Librerías: getpass, os, sys (estándar); src.autenticacion (propio)
# ---------------------------------------------------------------------
# Cambia la contraseña de un usuario sin tocar el código: genera el hash
# y la sentencia SQL lista para pegar en el SQL Editor de Supabase.
#
# Uso:  python scripts/generar_hash.py cocina
# =====================================================================

import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.autenticacion import hashear_password  # noqa: E402

if len(sys.argv) != 2:
    print("Uso: python scripts/generar_hash.py <usuario>")
    sys.exit(1)

usuario = sys.argv[1]
clave = getpass.getpass(f"Nueva contraseña para '{usuario}': ")   # no se muestra al escribir
if len(clave) < 8:
    print("La contraseña debe tener al menos 8 caracteres.")
    sys.exit(1)

print("\nPega esto en el SQL Editor de Supabase:\n")
print(f"update usuarios set password_hash = '{hashear_password(clave)}' where username = '{usuario}';")
