# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Evaluación N°3 - 26 de noviembre de 2026
# Archivo  : tests/test_repositorio.py
# ---------------------------------------------------------------------
# Pruebas de RepositorioSupabase, del servicio de registro y de los
# cálculos del panel (analisis.py) usando el cliente falso en memoria.
# =====================================================================

import pytest

from src.analisis import (
    calcular_kpis, construir_grafo, filtrar_por_menu, menus_relacionados,
    ordenar_historial, ranking_jerarquico, resumen_por_ingrediente,
    resumen_por_menu, top_ordenes_por_perdida,
)
from src.autenticacion import autenticar
from src.base_datos import ErrorBaseDatos, RepositorioSupabase
from src.modelos import Usuario
from src.servicios import registrar_orden
from tests.fakes import ClienteFalso

COCINA = Usuario(1, "cocina", "Cocina", "cocina", ve_costos=False, registra_ordenes=True)


def repo_con_ordenes():
    repo = RepositorioSupabase(ClienteFalso())
    recetas = {r.nombre: r for r in repo.obtener_recetas()}
    plan = [("Arroz con Pollo y Ensalada", 4), ("Arroz con Pollo y Ensalada", 11),
            ("Tortilla de Papas y Cebolla", 4), ("Papas Cocidas con Huevo y Lechuga", 25),
            ("Charquicán Simple", 8), ("Fideos con Huevo y Tomate", 4)]
    for menu, n in plan:
        registrar_orden(repo, COCINA, recetas[menu], n)
    return repo


def test_catalogo_completo_desde_la_bd():
    repo = RepositorioSupabase(ClienteFalso())
    recetas = repo.obtener_recetas()
    assert len(recetas) == 10 and len(repo.obtener_ingredientes()) == 10
    assert all(len(r.items) in (4,) for r in recetas)               # cada receta del enunciado tiene 4 líneas
    assert sum(len(r.items) for r in recetas) == 40
    assert repo.contar_registros_base() == {"ingredientes": 10, "recetas": 10, "usuarios": 2}
    assert recetas[0].buscar_item("lechuga").unidad_receta == "unidades"
    assert recetas[0].buscar_item("zapallo") is None


def test_login_contra_la_bd():
    repo = RepositorioSupabase(ClienteFalso())
    assert autenticar(repo.obtener_usuarios(), repo.obtener_roles(), "cocina", "Cocina2026!").rol == "cocina"
    assert autenticar(repo.obtener_usuarios(), repo.obtener_roles(), "admin", "Admin2026!").ve_costos
    assert autenticar(repo.obtener_usuarios(), repo.obtener_roles(), "admin", "Cocina2026!") is None


def test_registrar_orden_guarda_orden_y_detalle():
    repo = RepositorioSupabase(ClienteFalso())
    receta = repo.obtener_recetas()[0]
    orden_id, resultado = registrar_orden(repo, COCINA, receta, 4)
    ordenes, detalle = repo.obtener_ordenes(), repo.obtener_detalle_ordenes()
    assert len(ordenes) == 1 and ordenes[0]["id"] == orden_id
    assert ordenes[0]["menu"] == "Arroz con Pollo y Ensalada"
    assert ordenes[0]["costo_total"] == 8300 and ordenes[0]["perdida_merma"] == 2100
    assert len(detalle) == 4 and {d["ingrediente"] for d in detalle} == {"Trutro de pollo", "Arroz", "Lechuga", "Aceite"}
    assert sum(d["perdida_merma"] for d in detalle) == 2100


def test_registrar_orden_rechaza_entradas_invalidas_sin_guardar():
    repo = RepositorioSupabase(ClienteFalso())
    receta = repo.obtener_recetas()[0]
    for malo in (None, 0, -5, 2.5, ""):
        with pytest.raises(ValueError):
            registrar_orden(repo, COCINA, receta, malo)
    with pytest.raises(ValueError):
        registrar_orden(repo, COCINA, None, 4)
    assert repo.obtener_ordenes() == []                              # nada se guardó


def test_registrar_orden_sin_permiso():
    repo = RepositorioSupabase(ClienteFalso())
    sin_permiso = Usuario(9, "x", "X", "x", ve_costos=False, registra_ordenes=False)
    with pytest.raises(PermissionError):
        registrar_orden(repo, sin_permiso, repo.obtener_recetas()[0], 4)
    with pytest.raises(PermissionError):
        registrar_orden(repo, None, repo.obtener_recetas()[0], 4)


def test_si_falla_el_detalle_se_borra_la_orden():
    cliente = ClienteFalso()
    repo = RepositorioSupabase(cliente)
    receta = repo.obtener_recetas()[0]
    cliente.falla_detalle = True
    with pytest.raises(ErrorBaseDatos):
        registrar_orden(repo, COCINA, receta, 4)
    assert cliente.tablas["ordenes"] == []                          # no queda una orden a medias


def test_historial_de_cocina_no_trae_dinero():
    repo = repo_con_ordenes()
    filas = repo.obtener_ordenes_cocina()
    assert len(filas) == 6 and filas[0]["id"] > filas[-1]["id"]      # más reciente primero
    for f in filas:
        assert set(f) == {"id", "fecha", "comensales", "receta_id"}


def test_paginacion_con_mas_de_mil_filas():
    cliente = ClienteFalso()
    repo = RepositorioSupabase(cliente)
    for i in range(2300):
        cliente.tablas["ordenes"].append({"id": i + 1, "receta_id": 1, "comensales": 4})
    assert len(repo._traer_todo("ordenes", orden="id")) == 2300


def test_kpis_y_resumenes_coinciden_con_los_calculos():
    repo = repo_con_ordenes()
    ordenes, detalle = repo.obtener_ordenes(), repo.obtener_detalle_ordenes()
    k = calcular_kpis(ordenes)
    assert k["servicios"] == 6 and k["comensales"] == 4 + 11 + 4 + 25 + 8 + 4
    assert k["costo_total"] == sum(o["costo_total"] for o in ordenes)
    assert k["ingresos"] == round(k["costo_total"] * 1.25, 2)
    assert k["utilidad"] == round(k["ingresos"] - k["costo_total"], 2)
    # lo perdido en las órdenes debe ser igual a la suma del detalle por ingrediente
    assert round(sum(f["perdida_merma"] for f in resumen_por_ingrediente(detalle)), 2) == k["perdida_merma"]
    assert round(sum(f["perdida_merma"] for f in resumen_por_menu(ordenes)), 2) == k["perdida_merma"]
    menus = {f["menu"]: f for f in resumen_por_menu(ordenes)}
    assert menus["Arroz con Pollo y Ensalada"]["servicios"] == 2


def test_top_ordenes_y_ranking():
    repo = repo_con_ordenes()
    ordenes, detalle = repo.obtener_ordenes(), repo.obtener_detalle_ordenes()
    top = top_ordenes_por_perdida(ordenes, 3)
    perdidas = [o["perdida_merma"] for o in top]
    assert perdidas == sorted((o["perdida_merma"] for o in ordenes), reverse=True)[:3]
    ranking = ranking_jerarquico(resumen_por_ingrediente(detalle), "ingrediente", "perdida_merma")
    valores = [v for _, _, v in ranking]
    assert valores == sorted(valores, reverse=True) and ranking[0][0] == 1
    assert ranking[0][1] == "Huevo"                                  # el huevo (empaque de 12) es lo que más se pierde


@pytest.mark.parametrize("metodo", ["Merge sort", "Quicksort", "Inserción", "Burbuja", "Externo (merge por bloques)"])
def test_filtrar_y_ordenar_historial(metodo):
    repo = repo_con_ordenes()
    ordenes = repo.obtener_ordenes()
    arroz = filtrar_por_menu(ordenes, "Arroz con Pollo y Ensalada")
    assert len(arroz) == 2 and len(filtrar_por_menu(ordenes, "Todos")) == 6
    assert filtrar_por_menu(ordenes, "Menú inexistente") == []
    res, texto = ordenar_historial(ordenes, "perdida_merma", True, metodo, 2)
    assert [o["perdida_merma"] for o in res] == sorted((o["perdida_merma"] for o in ordenes), reverse=True)
    assert "comparaciones" in texto


def test_grafo_menu_ingrediente():
    recetas = RepositorioSupabase(ClienteFalso()).obtener_recetas()
    g = construir_grafo(recetas)
    assert len(g.vertices("menu")) == 10 and len(g.vertices("ingrediente")) == 10
    assert sorted(g.vecinos("Charquicán Simple")) == ["Aceite", "Cebolla", "Lechuga", "Papa"]
    rel = dict(menus_relacionados(g, "Charquicán Simple"))
    assert "Papas Cocidas con Huevo y Lechuga" in rel
    assert set(rel["Papas Cocidas con Huevo y Lechuga"]) == {"Papa", "Lechuga", "Aceite"}
