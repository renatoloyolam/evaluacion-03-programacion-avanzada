# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/servicios.py
# Librerías: ninguna externa; calculo.py (propio)
# ---------------------------------------------------------------------
# Capa intermedia entre la pantalla y el resto: junta el cálculo con el
# guardado en la base de datos. Así la interfaz no necesita saber
# cómo se calcula ni cómo se guarda, solo llama a registrar_orden().
# =====================================================================

from src.calculo import calcular_orden


def registrar_orden(repo, usuario, receta, comensales):
    """
    Calcula la orden y la guarda en la base de datos.
    Devuelve (orden_id, resultado). Si el usuario no tiene permiso de
    registrar órdenes se lanza PermissionError antes de tocar nada.
    """
    if usuario is None or not usuario.registra_ordenes:
        raise PermissionError("Este perfil no puede registrar órdenes.")
    resultado = calcular_orden(receta, comensales)      # valida entradas y calcula
    orden_id = repo.guardar_orden(resultado, usuario.id)  # persiste orden + detalle
    return orden_id, resultado
