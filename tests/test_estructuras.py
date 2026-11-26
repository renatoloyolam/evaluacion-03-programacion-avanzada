# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Evaluación N°3 - 26 de noviembre de 2026
# Archivo  : tests/test_estructuras.py
# ---------------------------------------------------------------------
# Pruebas de los TDAs, algoritmos de ordenamiento (interno y externo),
# búsqueda secuencial y autenticación.
# =====================================================================

import random

import pytest

from src.autenticacion import autenticar, exigir_costos, hashear_password, verificar_password
from src.busqueda import buscar_por_texto, buscar_secuencial, filtrar_secuencial, indice_secuencial
from src.estructuras import ArbolBinarioBusqueda, Cola, ColaPrioridad, Grafo, ListaEnlazada, Pila
from src.modelos import Usuario
from src.ordenamiento import ALGORITMOS_INTERNOS, ordenamiento_externo, ordenar


# ---------------- TDAs ----------------

def test_lista_enlazada():
    lista = ListaEnlazada([1, 2, 3])
    lista.agregar_final(4)
    lista.agregar_inicio(0)
    assert list(lista) == [0, 1, 2, 3, 4] and len(lista) == 5
    assert lista.eliminar(0) and lista.eliminar(4) and lista.eliminar(2)
    assert not lista.eliminar(99)
    assert list(lista) == [1, 3]
    lista.agregar_final(5)                  # la cola debe seguir bien tras borrar el último
    assert list(lista) == [1, 3, 5]
    vacia = ListaEnlazada()
    assert vacia.esta_vacia() and list(vacia) == []


def test_pila_lifo():
    p = Pila()
    for x in (1, 2, 3):
        p.apilar(x)
    assert p.cima() == 3 and list(p) == [3, 2, 1]
    assert [p.desapilar(), p.desapilar(), p.desapilar()] == [3, 2, 1]
    assert p.esta_vacia()
    with pytest.raises(IndexError):
        p.desapilar()
    with pytest.raises(IndexError):
        p.cima()


def test_cola_fifo():
    c = Cola()
    for x in "abc":
        c.encolar(x)
    assert c.frente() == "a" and list(c) == ["a", "b", "c"]
    assert c.desencolar() == "a"
    c.encolar("d")
    assert [c.desencolar() for _ in range(3)] == ["b", "c", "d"]
    assert c.esta_vacia()
    c.encolar("z")                          # reutilizable tras vaciarse
    assert c.desencolar() == "z"
    with pytest.raises(IndexError):
        c.desencolar()


def test_cola_prioridad_min_y_max():
    for mayor, esperado in ((False, [1, 2, 3, 5, 8]), (True, [8, 5, 3, 2, 1])):
        cp = ColaPrioridad(mayor_primero=mayor)
        for x in (5, 1, 8, 3, 2):
            cp.insertar(x, f"v{x}")
        assert [cp.extraer()[0] for _ in range(5)] == esperado
        assert cp.esta_vacia()
    with pytest.raises(IndexError):
        ColaPrioridad().extraer()


def test_cola_prioridad_empates_fifo():
    cp = ColaPrioridad(mayor_primero=True)
    for nombre in ("a", "b", "c"):
        cp.insertar(10, nombre)
    assert [cp.extraer()[1] for _ in range(3)] == ["a", "b", "c"]


def test_cola_prioridad_aleatoria_contra_sorted():
    random.seed(1)
    datos = [random.randint(0, 50) for _ in range(300)]
    cp = ColaPrioridad()
    for d in datos:
        cp.insertar(d, d)
    assert [cp.extraer()[0] for _ in range(len(datos))] == sorted(datos)


def test_arbol_binario_busqueda():
    abb = ArbolBinarioBusqueda()
    for k in (50, 30, 70, 20, 40, 60, 80, 30):          # 30 repetido
        abb.insertar(k, f"n{k}")
    assert [k for k, _ in abb.en_orden()] == [20, 30, 30, 40, 50, 60, 70, 80]
    assert [k for k, _ in abb.en_orden_inverso()] == [80, 70, 60, 50, 40, 30, 30, 20]
    assert abb.buscar(60) == "n60" and abb.buscar(99) is None
    assert len(abb) == 8 and abb.altura() == 4
    assert ArbolBinarioBusqueda().altura() == 0 and ArbolBinarioBusqueda().en_orden() == []


def test_arbol_muchos_datos_sin_recursion():
    abb = ArbolBinarioBusqueda()
    for i in range(3000):                               # peor caso: árbol degenerado (lista)
        abb.insertar(i, i)
    assert len(abb.en_orden()) == 3000 and abb.altura() == 3000


def test_grafo_bfs_y_comunes():
    g = Grafo()
    g.agregar_arista("M1", "papa")
    g.agregar_arista("M1", "aceite")
    g.agregar_arista("M2", "aceite")
    g.agregar_arista("M3", "huevo")
    g.agregar_arista("M1", "papa")                       # repetida: no debe duplicarse
    for m in ("M1", "M2", "M3"):
        g.agregar_vertice(m, "menu")
    assert g.vecinos("M1") == ["papa", "aceite"] and g.grado("aceite") == 2
    assert g.bfs("M1") == {"M1": 0, "papa": 1, "aceite": 1, "M2": 2}
    assert g.vecinos_comunes("M1", "M2") == ["aceite"]
    assert g.bfs("no_existe") == {}
    assert g.vertices("menu") == ["M1", "M2", "M3"]


# ---------------- Ordenamiento ----------------

@pytest.mark.parametrize("nombre", list(ALGORITMOS_INTERNOS))
@pytest.mark.parametrize("descendente", [False, True])
def test_ordenamiento_interno_correcto(nombre, descendente):
    random.seed(7)
    for n in (0, 1, 2, 3, 10, 57, 200):
        datos = [random.randint(-20, 20) for _ in range(n)]      # con repetidos
        original = list(datos)
        res, comps = ordenar(datos, descendente=descendente, algoritmo=nombre)
        assert res == sorted(original, reverse=descendente)
        assert datos == original                                    # no modifica la lista de entrada
        assert comps >= 0


@pytest.mark.parametrize("nombre", ["Merge sort", "Inserción", "Burbuja"])
def test_algoritmos_estables(nombre):
    # (clave, orden_original): los empates deben conservar el orden original
    datos = [(3, "a"), (1, "b"), (3, "c"), (1, "d"), (2, "e"), (3, "f")]
    res, _ = ordenar(datos, clave=lambda x: x[0], algoritmo=nombre)
    assert res == [(1, "b"), (1, "d"), (2, "e"), (3, "a"), (3, "c"), (3, "f")]


def test_quicksort_casos_dificiles():
    ya_ordenada = list(range(2000))
    assert ordenar(ya_ordenada, algoritmo="Quicksort")[0] == ya_ordenada
    inversa = list(range(2000, 0, -1))
    assert ordenar(inversa, algoritmo="Quicksort")[0] == sorted(inversa)
    iguales = [5] * 3000                                           # muchos repetidos: no debe ser cuadrático
    res, comps = ordenar(iguales, algoritmo="Quicksort")
    assert res == iguales and comps < 10_000


def test_orden_por_clave_de_diccionarios():
    regs = [{"id": 1, "p": 30.5}, {"id": 2, "p": 10.0}, {"id": 3, "p": 99.9}]
    res, _ = ordenar(regs, clave=lambda r: r["p"], descendente=True)
    assert [r["id"] for r in res] == [3, 1, 2]


def test_algoritmo_desconocido():
    with pytest.raises(ValueError):
        ordenar([3, 1], algoritmo="Magia")


@pytest.mark.parametrize("descendente", [False, True])
@pytest.mark.parametrize("tam_bloque", [1, 7, 50, 1000])
def test_ordenamiento_externo(descendente, tam_bloque):
    random.seed(3)
    regs = [{"id": i, "valor": random.randint(0, 40), "texto": f"menú ñ {i}"} for i in range(230)]
    res, info = ordenamiento_externo(regs, lambda r: r["valor"], descendente, tam_bloque)
    assert [r["valor"] for r in res] == sorted((r["valor"] for r in regs), reverse=descendente)
    assert sorted(r["id"] for r in res) == list(range(230))         # no pierde ni duplica registros
    assert info["registros"] == 230
    assert info["bloques"] == -(-230 // tam_bloque)                  # ceil(230 / tam_bloque)
    assert {r["texto"] for r in res} == {r["texto"] for r in regs}   # tildes/ñ sobreviven al archivo


def test_ordenamiento_externo_vacio_y_errores():
    res, info = ordenamiento_externo([], lambda r: r, False, 10)
    assert res == [] and info["bloques"] == 0
    with pytest.raises(ValueError):
        ordenamiento_externo([1], lambda r: r, False, 0)


def test_externo_con_fechas_y_decimales():
    regs = [{"f": "2026-11-0%d" % d, "x": d / 3} for d in (5, 2, 9, 1, 7)]
    res, _ = ordenamiento_externo(regs, lambda r: r["f"], False, 2)
    assert [r["f"] for r in res] == sorted(r["f"] for r in regs)


# ---------------- Búsqueda secuencial ----------------

def test_busqueda_secuencial():
    datos = ["Arroz", "Papa", "Tomate", "Papa"]
    assert buscar_secuencial(datos, lambda x: x == "Papa") == "Papa"
    assert buscar_secuencial(datos, lambda x: x == "Zapallo") is None
    assert indice_secuencial(datos, lambda x: x == "Tomate") == 2
    assert indice_secuencial(datos, lambda x: x == "Nada") == -1
    assert filtrar_secuencial(datos, lambda x: x == "Papa") == ["Papa", "Papa"]
    assert buscar_por_texto(datos, lambda x: x, "  tomate ") == "Tomate"
    assert buscar_por_texto(ListaEnlazada(datos), lambda x: x, "ARROZ") == "Arroz"     # también sobre la lista enlazada


# ---------------- Autenticación ----------------

ROLES = [{"rol": "cocina", "ve_costos": False, "registra_ordenes": True},
         {"rol": "administrador", "ve_costos": True, "registra_ordenes": True}]
USUARIOS = [
    {"id": 1, "username": "cocina", "nombre_completo": "Cocina", "rol": "cocina", "activo": True,
     "password_hash": hashear_password("clave1", iteraciones=1000)},
    {"id": 2, "username": "admin", "nombre_completo": "Admin", "rol": "administrador", "activo": True,
     "password_hash": hashear_password("clave2", iteraciones=1000)},
    {"id": 3, "username": "baja", "nombre_completo": "Baja", "rol": "cocina", "activo": False,
     "password_hash": hashear_password("clave3", iteraciones=1000)},
    {"id": 4, "username": "raro", "nombre_completo": "Raro", "rol": "inexistente", "activo": True,
     "password_hash": hashear_password("clave4", iteraciones=1000)},
]


def test_hash_con_sal_distinta_y_verificacion():
    h1, h2 = hashear_password("secreto"), hashear_password("secreto")
    assert h1 != h2                                                  # sal aleatoria
    assert verificar_password("secreto", h1) and verificar_password("secreto", h2)
    assert not verificar_password("otra", h1)
    assert "secreto" not in h1
    for malo in ("", "basura", "a$b$c$d", None, "pbkdf2_sha256$x$zz$zz"):
        assert verificar_password("secreto", malo) is False


def test_autenticar_roles_y_permisos():
    u = autenticar(USUARIOS, ROLES, "cocina", "clave1")
    assert u.rol == "cocina" and not u.ve_costos and u.registra_ordenes
    a = autenticar(USUARIOS, ROLES, "  ADMIN ", "clave2")           # ignora mayúsculas y espacios
    assert a.rol == "administrador" and a.ve_costos


@pytest.mark.parametrize("usuario,clave", [
    ("cocina", "mala"), ("nadie", "clave1"), ("", "clave1"), ("cocina", ""), (None, None),
    ("baja", "clave3"), ("raro", "clave4"),
])
def test_autenticar_rechaza(usuario, clave):
    assert autenticar(USUARIOS, ROLES, usuario, clave) is None


def test_exigir_costos():
    cocina = Usuario(1, "c", "C", "cocina", ve_costos=False, registra_ordenes=True)
    admin = Usuario(2, "a", "A", "administrador", ve_costos=True, registra_ordenes=True)
    exigir_costos(admin)
    with pytest.raises(PermissionError):
        exigir_costos(cocina)
    with pytest.raises(PermissionError):
        exigir_costos(None)
