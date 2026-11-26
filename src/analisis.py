# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/analisis.py
# Librerías: fractions (estándar); estructuras, ordenamiento, busqueda, modelos (propios)
# ---------------------------------------------------------------------
# Lógica del panel gerencial (Actividad 4) separada de la pantalla:
# KPIs, resúmenes por menú/ingrediente, filtros, ordenamientos y ranking de
# mermas. Recibe listas de diccionarios (las filas de Supabase) y devuelve
# listas/diccionarios, sin saber nada de Streamlit.
# =====================================================================

from fractions import Fraction

from src.busqueda import filtrar_secuencial
from src.estructuras import ArbolBinarioBusqueda, ColaPrioridad, Grafo
from src.modelos import a_fraccion
from src.ordenamiento import ordenamiento_externo, ordenar


def _suma(filas, campo):
    """Suma un campo de varias filas con Fraction (exacto) y devuelve un float redondeado a 2 decimales."""
    total = sum((a_fraccion(f[campo]) for f in filas), Fraction(0))
    return round(float(total), 2)


# ---------------------------------------------------------------------
# KPIs globales
# ---------------------------------------------------------------------

def calcular_kpis(ordenes):
    """Indicadores clave del resumen ejecutivo."""
    costo = _suma(ordenes, "costo_total")
    perdida = _suma(ordenes, "perdida_merma")
    ingresos = _suma(ordenes, "ingreso_total")
    return {
        "servicios": len(ordenes),
        "comensales": int(sum(int(o["comensales"]) for o in ordenes)),
        "costo_total": costo,
        "perdida_merma": perdida,
        "ingresos": ingresos,
        "utilidad": round(ingresos - costo, 2),
        "pct_merma": round(perdida / costo * 100, 2) if costo else 0.0,
    }


def top_ordenes_por_perdida(ordenes, k=5):
    """
    Las k órdenes con mayor pérdida por merma. Uso una ColaPrioridad (heap) con
    prioridad = pérdida, sacando primero la mayor. Es mejor que ordenar todo
    cuando solo interesan las primeras k.
    """
    cola = ColaPrioridad(mayor_primero=True)
    for o in ordenes:
        cola.insertar(float(o["perdida_merma"]), o)
    resultado = []
    while not cola.esta_vacia() and len(resultado) < k:
        _, orden = cola.extraer()
        resultado.append(orden)
    return resultado


# ---------------------------------------------------------------------
# Resúmenes agrupados
# ---------------------------------------------------------------------

def resumen_por_menu(ordenes):
    """Agrupa las órdenes por menú: servicios, comensales, costo, pérdida, ingresos y % de merma."""
    grupos = {}
    for o in ordenes:
        g = grupos.setdefault(o["menu"], {"menu": o["menu"], "servicios": 0, "comensales": 0,
                                          "costo_total": Fraction(0), "perdida_merma": Fraction(0),
                                          "ingreso_total": Fraction(0)})
        g["servicios"] += 1
        g["comensales"] += int(o["comensales"])
        g["costo_total"] += a_fraccion(o["costo_total"])
        g["perdida_merma"] += a_fraccion(o["perdida_merma"])
        g["ingreso_total"] += a_fraccion(o["ingreso_total"])
    filas = []
    for g in grupos.values():
        costo = g["costo_total"]
        filas.append({
            "menu": g["menu"],
            "servicios": g["servicios"],
            "comensales": g["comensales"],
            "costo_total": round(float(costo), 2),
            "perdida_merma": round(float(g["perdida_merma"]), 2),
            "ingreso_total": round(float(g["ingreso_total"]), 2),
            "pct_merma": round(float(g["perdida_merma"] / costo * 100), 2) if costo else 0.0,
        })
    return filas


def resumen_por_ingrediente(detalle):
    """Agrupa el detalle por ingrediente: envases consumidos, costo, merma y pérdida acumulada."""
    grupos = {}
    for d in detalle:
        g = grupos.setdefault(d["ingrediente"], {"ingrediente": d["ingrediente"],
                                                 "unidad_compra": d.get("unidad_compra", ""),
                                                 "envases": 0, "merma_envases": Fraction(0),
                                                 "costo_envases": Fraction(0), "perdida_merma": Fraction(0)})
        g["envases"] += int(d["envases_requeridos"])
        g["merma_envases"] += a_fraccion(d["merma_envases"])
        g["costo_envases"] += a_fraccion(d["costo_envases"])
        g["perdida_merma"] += a_fraccion(d["perdida_merma"])
    filas = []
    for g in grupos.values():
        costo = g["costo_envases"]
        filas.append({
            "ingrediente": g["ingrediente"],
            "unidad_compra": g["unidad_compra"],
            "envases": g["envases"],
            "merma_envases": round(float(g["merma_envases"]), 2),
            "costo_envases": round(float(costo), 2),
            "perdida_merma": round(float(g["perdida_merma"]), 2),
            "pct_merma": round(float(g["perdida_merma"] / costo * 100), 2) if costo else 0.0,
        })
    return filas


def ranking_jerarquico(filas, campo_nombre, campo_valor):
    """
    Ranking de mayor a menor construido con un Árbol Binario de Búsqueda.
    La clave es (valor, nombre): el nombre desempata y evita claves idénticas.
    El recorrido inorden inverso entrega la jerarquía de mayor a menor pérdida.
    Devuelve una lista de (posición, nombre, valor).
    """
    arbol = ArbolBinarioBusqueda()
    for f in filas:
        arbol.insertar((float(f[campo_valor]), str(f[campo_nombre])), f)
    ranking = []
    for posicion, (clave, fila) in enumerate(arbol.en_orden_inverso(), start=1):
        ranking.append((posicion, fila[campo_nombre], clave[0]))
    return ranking


# ---------------------------------------------------------------------
# Filtro y ordenamiento del historial
# ---------------------------------------------------------------------

def filtrar_por_menu(ordenes, menu):
    """Filtra con búsqueda secuencial. menu=None o 'Todos' devuelve todo."""
    if not menu or menu == "Todos":
        return list(ordenes)
    return filtrar_secuencial(ordenes, lambda o: o["menu"] == menu)


def ordenar_historial(ordenes, columna, descendente, metodo, tam_bloque=50):
    """
    Ordena el historial por 'columna'.
      - metodo 'Externo (merge por bloques)': usa ordenamiento_externo (archivos temporales)
      - cualquier otro: algoritmo interno con ese nombre
    Devuelve (lista_ordenada, texto_descriptivo) para mostrar qué se hizo.
    """
    if metodo.startswith("Externo"):
        lista, info = ordenamiento_externo(ordenes, lambda o: o[columna], descendente, tam_bloque)
        texto = (f"Ordenamiento externo: {info['registros']} registros en {info['bloques']} bloque(s) "
                 f"de hasta {info['tam_bloque']}, {info['comparaciones']} comparaciones.")
        return lista, texto
    lista, comps = ordenar(ordenes, lambda o: o[columna], descendente, metodo)
    return lista, f"{metodo}: {len(lista)} registros, {comps} comparaciones."


# ---------------------------------------------------------------------
# Grafo menú <-> ingrediente
# ---------------------------------------------------------------------

def construir_grafo(recetas):
    """Grafo bipartito: cada menú se conecta con los ingredientes de su receta."""
    grafo = Grafo()
    for receta in recetas:
        grafo.agregar_vertice(receta.nombre, "menu")
        for item in receta.items:
            grafo.agregar_vertice(item.ingrediente.nombre, "ingrediente")
            grafo.agregar_arista(receta.nombre, item.ingrediente.nombre)
    return grafo


def menus_relacionados(grafo, menu):
    """
    Para un menú, qué otros menús comparten ingredientes (distancia 2 en el
    grafo) y cuáles son. Sirve para sugerir combinar servicios y así
    aprovechar envases abiertos.
    """
    distancias = grafo.bfs(menu)
    relacionados = []
    for vertice, dist in distancias.items():
        if dist == 2 and grafo.tipo(vertice) == "menu":
            relacionados.append((vertice, grafo.vecinos_comunes(menu, vertice)))
    relacionados.sort(key=lambda par: (-len(par[1]), par[0]))
    return relacionados
