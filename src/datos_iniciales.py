# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/datos_iniciales.py
# Librerías: fractions (estándar); modelos.py (propio)
# ---------------------------------------------------------------------
# Los 10 ingredientes y las 10 recetas del enunciado, tal cual vienen en
# la tabla. De acá sale el script sql/02_datos_iniciales.sql (lo genera
# scripts/generar_sql.py) y también los tests, así los datos son los mismos
# en todos lados y no hay que copiarlos a mano.
#
# Instrucción verbal del profesor: la "Utilidad" de la Cebolla es para 4 personas
# (la tabla impresa del enunciado dice "2 personas"). Se usa 4.
#
# Observaciones sobre el enunciado (las dejé como vienen, sin "arreglarlas"):
#   - La tabla dice "Tuto de pollo": lo escribí como "Trutro de pollo".
#   - "Carne Molida con Papas y Arroz" en la lista de ingredientes NO lleva arroz.
#   - "Charquicán Simple" tampoco lleva carne.
#   - "Carne Molida con Arroz y Ensalada" no lleva aceite.
# =====================================================================

from fractions import Fraction

from src.modelos import Ingrediente, ItemReceta, Receta

# (nombre, unidad de compra, costo por unidad de compra en $, personas que rinde, texto original de "Utilidad")
INGREDIENTES = [
    ("Cebolla",         "unidad",  500,  4,  "4 personas"),
    ("Arroz",           "paquete", 1500, 10, "10 personas por paquete"),
    ("Trutro de pollo", "unidad",  1200, 1,  "1 por persona"),
    ("Carne molida",    "paquete", 1500, 4,  "4 personas por paquete"),
    ("Papa",            "kg",      1000, 4,  "4 personas por kg"),
    ("Tomate",          "kg",      1500, 6,  "6 personas por kg"),
    ("Fideos",          "paquete", 1200, 4,  "4 personas por paquete"),
    ("Lechuga",         "unidad",  1000, 10, "10 personas por lechuga"),
    ("Huevo",           "empaque", 4500, 12, "12 personas por empaque"),
    ("Aceite",          "litro",   1000, 10, "10 personas por litro"),
]

# (nombre de la receta, base de comensales, [(ingrediente, cantidad, unidad en la receta), ...])
RECETAS = [
    ("Arroz con Pollo y Ensalada", 4, [
        ("Trutro de pollo", 4, "unidades"), ("Arroz", 4, "porciones"),
        ("Lechuga", 1, "unidades"), ("Aceite", 4, "porciones")]),
    ("Carne Molida con Papas y Arroz", 4, [
        ("Carne molida", 4, "porciones"), ("Papa", 6, "unidades"),
        ("Cebolla", 1, "unidades"), ("Aceite", 4, "porciones")]),
    ("Tallarines con Salsa de Tomate", 4, [
        ("Fideos", 4, "porciones"), ("Tomate", 4, "unidades"),
        ("Cebolla", 1, "unidades"), ("Aceite", 4, "porciones")]),
    ("Tortilla de Papas y Cebolla", 4, [
        ("Papa", 6, "unidades"), ("Cebolla", 1, "unidades"),
        ("Huevo", 6, "unidades"), ("Aceite", 4, "porciones")]),
    ("Pollo Salteado con Verduras", 4, [
        ("Trutro de pollo", 4, "unidades"), ("Tomate", 3, "unidades"),
        ("Cebolla", 1, "unidades"), ("Aceite", 4, "porciones")]),
    ("Charquicán Simple", 4, [
        ("Papa", 6, "unidades"), ("Lechuga", 1, "unidades"),
        ("Cebolla", 1, "unidades"), ("Aceite", 4, "porciones")]),
    ("Fideos con Huevo y Tomate", 4, [
        ("Fideos", 4, "porciones"), ("Huevo", 4, "unidades"),
        ("Tomate", 3, "unidades"), ("Aceite", 4, "porciones")]),
    ("Carne Molida con Arroz y Ensalada", 4, [
        ("Carne molida", 4, "porciones"), ("Arroz", 4, "porciones"),
        ("Lechuga", 1, "unidades"), ("Tomate", 2, "unidades")]),
    ("Papas Cocidas con Huevo y Lechuga", 4, [
        ("Papa", 6, "unidades"), ("Huevo", 4, "unidades"),
        ("Lechuga", 1, "unidades"), ("Aceite", 4, "porciones")]),
    ("Arroz Graneado con Huevo y Cebolla", 4, [
        ("Arroz", 4, "porciones"), ("Huevo", 4, "unidades"),
        ("Cebolla", 1, "unidades"), ("Aceite", 4, "porciones")]),
]


def construir_catalogo():
    """
    Arma objetos Ingrediente y Receta en memoria (con ids 1..n en el mismo orden
    de las listas de arriba). Sirve para los tests y para probar sin base de datos.
    Devuelve (lista_de_ingredientes, lista_de_recetas).
    """
    ingredientes = []
    for i, (nombre, unidad, costo, personas, _) in enumerate(INGREDIENTES, start=1):
        ingredientes.append(Ingrediente(i, nombre, unidad, Fraction(costo), personas))
    por_nombre = {ing.nombre: ing for ing in ingredientes}

    recetas = []
    for i, (nombre, base, items) in enumerate(RECETAS, start=1):
        receta = Receta(i, nombre, base)
        for ing_nombre, cantidad, unidad_receta in items:
            receta.agregar_item(ItemReceta(por_nombre[ing_nombre], Fraction(cantidad), unidad_receta))
        recetas.append(receta)
    return ingredientes, recetas
