# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/ordenamiento.py
# Librerías: json, os, tempfile (estándar); estructuras.py (propio)
# ---------------------------------------------------------------------
# Algoritmos de ordenamiento hechos a mano.
#   INTERNOS (5.1): burbuja, inserción, quicksort y merge sort. Trabajan
#                   con todo el arreglo en memoria.
#   EXTERNO  (5.2): merge sort externo. Parte los registros en bloques que
#                   sí caben en memoria, ordena cada bloque, lo guarda en un
#                   archivo temporal y después fusiona todos los archivos.
#
# Todas las funciones reciben:
#   datos       -> lista (o iterable) de registros
#   clave       -> función que saca de cada registro el valor por el que se ordena
#   descendente -> True para ordenar de mayor a menor
# y devuelven (lista_ordenada, cantidad_de_comparaciones) para poder mostrar
# en pantalla cuánto trabajo hizo cada algoritmo.
# =====================================================================

import json
import os
import tempfile

from src.estructuras import ColaPrioridad, Pila


def _antes(a, b, clave, descendente):
    """True si el registro 'a' debe quedar ANTES que 'b' (comparación estricta)."""
    if descendente:
        return clave(a) > clave(b)
    return clave(a) < clave(b)


# ---------------------------------------------------------------------
# ORDENAMIENTO INTERNO
# ---------------------------------------------------------------------

def burbuja(datos, clave=lambda x: x, descendente=False):
    """
    Burbuja: compara vecinos y los intercambia si están al revés.
    O(n²). Es estable. Corta antes si en una pasada no hubo intercambios.
    """
    a = list(datos)                        # trabajo sobre una copia, no toco la original
    comparaciones = 0
    n = len(a)
    for i in range(n - 1):
        hubo_cambio = False
        for j in range(n - 1 - i):         # lo último de cada pasada ya está en su lugar
            comparaciones += 1
            if _antes(a[j + 1], a[j], clave, descendente):
                a[j], a[j + 1] = a[j + 1], a[j]
                hubo_cambio = True
        if not hubo_cambio:                # ya estaba ordenada
            break
    return a, comparaciones


def insercion(datos, clave=lambda x: x, descendente=False):
    """
    Inserción: va armando una parte ordenada a la izquierda e inserta cada
    elemento nuevo en su posición. O(n²) pero muy rápida si ya viene casi ordenada.
    """
    a = list(datos)
    comparaciones = 0
    for i in range(1, len(a)):
        actual = a[i]
        j = i - 1
        while j >= 0:
            comparaciones += 1
            if _antes(actual, a[j], clave, descendente):
                a[j + 1] = a[j]            # corro el elemento hacia la derecha
                j -= 1
            else:
                break
        a[j + 1] = actual
    return a, comparaciones


def quicksort(datos, clave=lambda x: x, descendente=False):
    """
    Quicksort en el mismo arreglo (in-place) con partición en tres zonas
    (menores / iguales / mayores al pivote), para que no se ponga lento si hay
    muchos valores repetidos (por ejemplo muchas órdenes con merma 0).
    Uso una Pila propia en vez de recursión, así no hay límite de profundidad.
    Promedio O(n log n). No es estable.
    """
    a = list(datos)
    comparaciones = 0
    pila = Pila()
    pila.apilar((0, len(a) - 1))
    while not pila.esta_vacia():
        bajo, alto = pila.desapilar()
        if bajo >= alto:
            continue
        pivote = a[(bajo + alto) // 2]     # pivote al medio: evita el peor caso en listas ya ordenadas
        menor, i, mayor = bajo, bajo, alto
        while i <= mayor:
            comparaciones += 1
            if _antes(a[i], pivote, clave, descendente):
                a[menor], a[i] = a[i], a[menor]
                menor += 1
                i += 1
            elif _antes(pivote, a[i], clave, descendente):
                a[i], a[mayor] = a[mayor], a[i]
                mayor -= 1
            else:                          # igual al pivote: se queda en el medio
                i += 1
        pila.apilar((bajo, menor - 1))     # zona de los "antes del pivote"
        pila.apilar((mayor + 1, alto))     # zona de los "después del pivote"
    return a, comparaciones


def merge_sort(datos, clave=lambda x: x, descendente=False):
    """
    Merge sort: divide por la mitad, ordena cada mitad y las mezcla.
    O(n log n) siempre y es estable (los empates mantienen su orden original).
    """
    contador = [0]                         # lista de 1 elemento para poder modificarlo desde la función interna

    def mezclar(izq, der):
        resultado = []
        i = j = 0
        while i < len(izq) and j < len(der):
            contador[0] += 1
            # Si el de la derecha va estrictamente antes, sale primero. En empate sale el
            # de la izquierda: eso es lo que mantiene la estabilidad.
            if _antes(der[j], izq[i], clave, descendente):
                resultado.append(der[j])
                j += 1
            else:
                resultado.append(izq[i])
                i += 1
        resultado.extend(izq[i:])          # lo que sobre de alguna de las dos mitades
        resultado.extend(der[j:])
        return resultado

    def dividir(lista):
        if len(lista) <= 1:
            return lista
        medio = len(lista) // 2
        return mezclar(dividir(lista[:medio]), dividir(lista[medio:]))

    return dividir(list(datos)), contador[0]


# Diccionario para elegir el algoritmo por nombre desde la interfaz
ALGORITMOS_INTERNOS = {
    "Merge sort": merge_sort,
    "Quicksort": quicksort,
    "Inserción": insercion,
    "Burbuja": burbuja,
}


def ordenar(datos, clave=lambda x: x, descendente=False, algoritmo="Merge sort"):
    """Ordena con el algoritmo interno indicado. Devuelve (lista, comparaciones)."""
    if algoritmo not in ALGORITMOS_INTERNOS:
        raise ValueError(f"Algoritmo desconocido: {algoritmo}")
    return ALGORITMOS_INTERNOS[algoritmo](datos, clave, descendente)


# ---------------------------------------------------------------------
# ORDENAMIENTO EXTERNO (merge sort por bloques con archivos temporales)
# ---------------------------------------------------------------------

def ordenamiento_externo(registros, clave, descendente=False, tam_bloque=50):
    """
    Merge sort externo en dos fases:

    Fase 1 (generar corridas): leo hasta 'tam_bloque' registros, los ordeno en
        memoria con merge sort y los escribo a un archivo temporal (una línea
        JSON por registro). Eso es una "corrida" ordenada.
    Fase 2 (fusión de K vías): abro todas las corridas a la vez y, usando una
        cola de prioridad con el primer registro de cada archivo, voy sacando
        siempre el menor (o mayor). Así en memoria solo hay K registros a la vez.

    Los registros deben poder pasar por JSON (diccionarios con texto/números).
    Devuelve (lista_ordenada, info) donde info trae bloques, tamaño y comparaciones.
    """
    if tam_bloque < 1:
        raise ValueError("El tamaño de bloque debe ser al menos 1")

    comparaciones = 0
    total = 0
    with tempfile.TemporaryDirectory() as carpeta:      # se borra sola al terminar
        rutas = []

        # ---- Fase 1: generar las corridas ordenadas ----
        bloque = []

        def volcar_bloque(bloque_actual):
            nonlocal comparaciones
            ordenado, comps = merge_sort(bloque_actual, clave, descendente)
            comparaciones += comps
            ruta = os.path.join(carpeta, f"corrida_{len(rutas)}.jsonl")
            with open(ruta, "w", encoding="utf-8") as f:
                for reg in ordenado:
                    f.write(json.dumps(reg, default=str, ensure_ascii=False) + "\n")
            rutas.append(ruta)

        for registro in registros:
            bloque.append(registro)
            total += 1
            if len(bloque) == tam_bloque:
                volcar_bloque(bloque)
                bloque = []
        if bloque:                                       # último bloque, puede ser más chico
            volcar_bloque(bloque)

        # ---- Fase 2: fusión de todas las corridas ----
        archivos = [open(r, "r", encoding="utf-8") for r in rutas]
        try:
            cola = ColaPrioridad(mayor_primero=descendente)
            # Meto el primer registro de cada archivo. La prioridad es la clave del registro
            # y guardo también de qué archivo vino para saber de dónde reponer.
            for idx, f in enumerate(archivos):
                linea = f.readline()
                if linea:
                    reg = json.loads(linea)
                    cola.insertar(clave(reg), (idx, reg))

            resultado = []
            while not cola.esta_vacia():
                _, (idx, reg) = cola.extraer()
                resultado.append(reg)
                linea = archivos[idx].readline()                 # repongo desde el mismo archivo
                if linea:
                    nuevo = json.loads(linea)
                    cola.insertar(clave(nuevo), (idx, nuevo))
            comparaciones += cola.comparaciones              # comparaciones reales hechas por el heap
        finally:
            for f in archivos:
                f.close()

    info = {
        "bloques": len(rutas),
        "tam_bloque": tam_bloque,
        "registros": total,
        "comparaciones": comparaciones,
    }
    return resultado, info
