# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Evaluación N°3 - 26 de noviembre de 2026
# Archivo  : scripts/generar_sql.py
# Librerías: os, sys (estándar); src.datos_iniciales y src.autenticacion (propios)
# ---------------------------------------------------------------------
# Genera sql/02_datos_iniciales.sql a partir de src/datos_iniciales.py, para que
# los 10 ingredientes y las 10 recetas de la BD sean EXACTAMENTE los del código.
#
# Uso (desde la carpeta raíz del proyecto):
#     python scripts/generar_sql.py
#
# Si quieres cambiar las contraseñas iniciales, edita USUARIOS abajo y vuelve a correrlo.
# =====================================================================

import os
import sys

# Para poder importar "src" aunque se ejecute desde la carpeta scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.autenticacion import hashear_password   # noqa: E402
from src.datos_iniciales import INGREDIENTES, RECETAS   # noqa: E402

# (username, nombre completo, contraseña inicial, rol)
USUARIOS = [
    ("cocina", "Operador de Cocina", "Cocina2026!", "cocina"),
    ("admin", "Administrador del Casino", "Admin2026!", "administrador"),
]


def q(texto):
    """Escapa comillas simples para SQL."""
    return "'" + str(texto).replace("'", "''") + "'"


def generar():
    lineas = []
    lineas.append("-- =====================================================================")
    lineas.append("-- Alumno   : Renato Loyola Muñoz")
    lineas.append("-- Curso    : I CRIM Sistemas de Armas - Programación Avanzada")
    lineas.append("-- Evaluación N°3 - 26 de noviembre de 2026")
    lineas.append("-- Archivo  : sql/02_datos_iniciales.sql  (GENERADO con scripts/generar_sql.py)")
    lineas.append("-- Ejecutar DESPUÉS de sql/01_esquema.sql.")
    lineas.append("-- Carga: 2 roles, 2 usuarios, 10 ingredientes, 10 recetas y sus 40 líneas de ingredientes.")
    lineas.append("-- =====================================================================")
    lineas.append("")

    lineas.append("-- Roles y permisos")
    lineas.append("insert into roles (rol, descripcion, ve_costos, registra_ordenes) values")
    lineas.append("  ('cocina',        'Operador de cocina: solo ve cantidades a preparar', false, true),")
    lineas.append("  ('administrador', 'Acceso total: costos, mermas, ventas y panel gerencial', true, true);")
    lineas.append("")

    lineas.append("-- Usuarios (la contraseña va como hash PBKDF2, ver README para las claves iniciales)")
    lineas.append("insert into usuarios (username, nombre_completo, password_hash, rol) values")
    filas = []
    for username, nombre, clave, rol in USUARIOS:
        filas.append(f"  ({q(username)}, {q(nombre)}, {q(hashear_password(clave))}, {q(rol)})")
    lineas.append(",\n".join(filas) + ";")
    lineas.append("")

    lineas.append("-- Los 10 ingredientes de la tabla del enunciado")
    lineas.append("insert into ingredientes (nombre, unidad_compra, costo_unitario, personas_por_unidad, descripcion_utilidad) values")
    filas = [f"  ({q(n)}, {q(u)}, {c}, {p}, {q(d)})" for n, u, c, p, d in INGREDIENTES]
    lineas.append(",\n".join(filas) + ";")
    lineas.append("")

    lineas.append("-- Las 10 recetas (base de 4 comensales)")
    lineas.append("insert into recetas (nombre, base_comensales) values")
    filas = [f"  ({q(n)}, {b})" for n, b, _ in RECETAS]
    lineas.append(",\n".join(filas) + ";")
    lineas.append("")

    lineas.append("-- Ingredientes de cada receta (se enlazan por nombre, así no dependen de los ids)")
    lineas.append("insert into receta_ingredientes (receta_id, ingrediente_id, cantidad, unidad_receta)")
    lineas.append("select r.id, i.id, v.cantidad, v.unidad_receta")
    lineas.append("from (values")
    filas = []
    for receta, _, items in RECETAS:
        for ing, cant, unidad in items:
            filas.append(f"  ({q(receta)}, {q(ing)}, {cant}, {q(unidad)})")
    lineas.append(",\n".join(filas))
    lineas.append(") as v(receta, ingrediente, cantidad, unidad_receta)")
    lineas.append("join recetas r      on r.nombre = v.receta")
    lineas.append("join ingredientes i on i.nombre = v.ingrediente;")
    lineas.append("")

    lineas.append("-- Verificación rápida: deben salir 2 / 2 / 10 / 10 / 40")
    lineas.append("select (select count(*) from roles)               as roles,")
    lineas.append("       (select count(*) from usuarios)            as usuarios,")
    lineas.append("       (select count(*) from ingredientes)        as ingredientes,")
    lineas.append("       (select count(*) from recetas)             as recetas,")
    lineas.append("       (select count(*) from receta_ingredientes) as lineas_receta;")
    return "\n".join(lineas) + "\n"


if __name__ == "__main__":
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql", "02_datos_iniciales.sql")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(generar())
    print(f"Archivo generado: {ruta}")
