# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/busqueda.py
# Librerías: ninguna externa
# ---------------------------------------------------------------------
# Búsqueda secuencial (contenido 5.3). Se usa en tres lugares:
#   - consultar insumos / menús por nombre (catálogo)
#   - validar el acceso del usuario (buscar el username en la lista)
#   - filtrar el historial de órdenes por menú
# Elegí búsqueda secuencial (y no binaria) porque las listas son chicas y
# no vienen ordenadas, y así no hay que ordenar antes de cada consulta.
# =====================================================================


def buscar_secuencial(coleccion, criterio):
    """
    Recorre la colección elemento por elemento y devuelve el PRIMERO que
    cumple 'criterio' (una función que recibe el elemento y devuelve True/False).
    Si no hay ninguno, devuelve None. Peor caso: revisa todo, O(n).
    """
    for elemento in coleccion:
        if criterio(elemento):
            return elemento
    return None


def indice_secuencial(coleccion, criterio):
    """Igual que la anterior pero devuelve la posición (o -1 si no existe)."""
    posicion = 0
    for elemento in coleccion:
        if criterio(elemento):
            return posicion
        posicion += 1
    return -1


def filtrar_secuencial(coleccion, criterio):
    """Devuelve TODOS los elementos que cumplen el criterio (recorre una sola vez)."""
    encontrados = []
    for elemento in coleccion:
        if criterio(elemento):
            encontrados.append(elemento)
    return encontrados


def buscar_por_texto(coleccion, obtener_texto, texto_buscado):
    """
    Busca el primer elemento cuyo texto coincide, ignorando mayúsculas y
    espacios de los costados. 'obtener_texto' extrae el texto del elemento,
    por ejemplo: lambda ing: ing.nombre
    """
    buscado = str(texto_buscado).strip().lower()
    return buscar_secuencial(
        coleccion, lambda e: str(obtener_texto(e)).strip().lower() == buscado
    )
