# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/calculo.py
# Librerías: math, fractions, decimal (estándar); config.py y modelos.py (propios)
# ---------------------------------------------------------------------
# Motor de cálculo (Actividad 2). Son funciones puras: no tocan la base de
# datos ni Streamlit, así se pueden probar solas (ver tests/test_calculo.py).
#
# Reglas del enunciado que se aplican acá:
#   1. Ningún producto es divisible ni se puede guardar -> envases = math.ceil(...)
#   2. Se paga el envase completo, se use todo o no.
#   3. Merma física = lo que queda sin usar del envase (se bota).
#   4. Pérdida por merma = merma física valorizada en pesos.
#   5. Costo por plato = costo total de los envases / comensales.
#   6. Precio de venta = costo + 25 % de ganancia.
#
# Uso Fraction (fracciones exactas) para todas las cuentas y recién redondeo
# al mostrar o guardar. Con float pueden aparecer errores de representación
# (0.1 + 0.2 da 0.30000000000000004) y en dinero prefiero que los totales
# cuadren exactamente: costo por plato * comensales = costo total.
# =====================================================================

import math
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

from src.config import BASE_MARGEN, MARGEN_GANANCIA, MAX_COMENSALES, MODO_DEMANDA
from src.modelos import LineaInsumo, ResultadoOrden, a_fraccion


# ---------------------------------------------------------------------
# Validaciones de entrada
# ---------------------------------------------------------------------

def validar_comensales(valor, maximo=MAX_COMENSALES):
    """
    Valida la cantidad de comensales y la devuelve como int.
    Rechaza: vacío/nulo, texto, decimales, negativos y cero (y también
    un tope máximo para evitar errores de tipeo). Si algo está mal lanza
    ValueError con un mensaje que se le puede mostrar directo al usuario.
    """
    if valor is None:
        raise ValueError("Debe ingresar la cantidad de comensales (el campo está vacío).")
    if isinstance(valor, bool):             # True/False son int en Python; los descarto
        raise ValueError("La cantidad de comensales debe ser un número entero.")

    if isinstance(valor, str):
        texto = valor.strip()
        if texto == "":
            raise ValueError("Debe ingresar la cantidad de comensales (el campo está vacío).")
        try:
            valor = float(texto.replace(",", "."))
        except ValueError:
            raise ValueError("La cantidad de comensales debe ser un número.")

    if isinstance(valor, float):
        if math.isnan(valor) or math.isinf(valor):
            raise ValueError("La cantidad de comensales no es un número válido.")
        if not valor.is_integer():
            raise ValueError("La cantidad de comensales debe ser un número entero (sin decimales).")
        valor = int(valor)

    if not isinstance(valor, int):
        raise ValueError("La cantidad de comensales debe ser un número entero.")

    if valor == 0:
        raise ValueError("La cantidad de comensales no puede ser cero.")
    if valor < 0:
        raise ValueError("La cantidad de comensales no puede ser negativa.")
    if valor > maximo:
        raise ValueError(f"La cantidad máxima por servicio es {maximo} comensales.")
    return valor


def validar_menu(receta):
    """Verifica que se haya elegido un menú (no None)."""
    if receta is None:
        raise ValueError("Debe seleccionar un tipo de menú.")
    return receta


# ---------------------------------------------------------------------
# Redondeo
# ---------------------------------------------------------------------

def redondear(valor, decimales=2):
    """
    Pasa una Fraction a float con 'decimales' decimales, redondeando
    mitades hacia arriba (2.5 -> 3), que es lo que se espera en dinero.
    """
    valor = a_fraccion(valor)
    d = Decimal(valor.numerator) / Decimal(valor.denominator)
    return float(d.quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_UP))


# ---------------------------------------------------------------------
# Motor principal
# ---------------------------------------------------------------------

def calcular_linea(item, comensales, base_comensales, modo=MODO_DEMANDA):
    """
    Calcula un ingrediente de la receta para 'comensales' personas.

    Pasos:
      a) Cantidad a preparar = cantidad de la receta * comensales / base, redondeada
         hacia arriba (no se puede usar media papa si todo es indivisible).
      b) Demanda: lo que hay que cubrir con los envases. En modo "comensales"
         es la cantidad de personas; en modo "receta" es la cantidad a preparar exacta.
      c) Envases = ceil(demanda / personas_por_unidad)  <- la regla de indivisibilidad.
      d) Capacidad comprada = envases * personas_por_unidad.
      e) Merma = capacidad comprada - demanda (siempre >= 0 porque el ceil sube).
      f) Costo = envases * costo unitario; Pérdida = (merma / personas_por_unidad) * costo.
    """
    ing = item.ingrediente
    factor = Fraction(comensales, base_comensales)
    cantidad_exacta = item.cantidad * factor
    cantidad_preparar = math.ceil(cantidad_exacta)

    if modo == "receta":
        demanda = cantidad_exacta
    elif modo == "comensales":
        demanda = Fraction(comensales)
    else:
        raise ValueError(f"Modo de demanda desconocido: {modo}")

    envases = math.ceil(demanda / ing.personas_por_unidad)
    capacidad = Fraction(envases * ing.personas_por_unidad)
    merma_porciones = capacidad - demanda
    merma_envases = merma_porciones / ing.personas_por_unidad
    costo_envases = envases * ing.costo_unitario
    perdida = merma_envases * ing.costo_unitario

    return LineaInsumo(
        ingrediente=ing,
        cantidad_preparar=cantidad_preparar,
        unidad_receta=item.unidad_receta,
        envases=envases,
        capacidad_porciones=capacidad,
        merma_porciones=merma_porciones,
        merma_envases=merma_envases,
        costo_envases=costo_envases,
        perdida_merma=perdida,
    )


def calcular_precio_venta_total(costo_total, margen=MARGEN_GANANCIA, base=BASE_MARGEN):
    """
    Ingreso total por la venta del servicio.
      - sobre_costo: costo * (1 + margen)
      - sobre_venta: costo / (1 - margen)  (el margen es un % del precio final)
    """
    margen = a_fraccion(margen)
    if base == "sobre_costo":
        return costo_total * (1 + margen)
    if base == "sobre_venta":
        return costo_total / (1 - margen)
    raise ValueError(f"Base de margen desconocida: {base}")


def calcular_orden(receta, comensales, margen=MARGEN_GANANCIA, modo=MODO_DEMANDA, base_margen=BASE_MARGEN):
    """
    Calcula una orden completa (menú + comensales) y devuelve un ResultadoOrden.
    Es el único punto de entrada que usa la interfaz.
    """
    validar_menu(receta)
    comensales = validar_comensales(comensales)

    lineas = [calcular_linea(item, comensales, receta.base_comensales, modo) for item in receta.items]

    # Totales: sumo las líneas (todo en Fraction, sin errores de redondeo)
    costo_total = sum((l.costo_envases for l in lineas), Fraction(0))
    perdida_total = sum((l.perdida_merma for l in lineas), Fraction(0))
    merma_fisica = sum((l.merma_envases for l in lineas), Fraction(0))

    # Costo por plato = costo total de los productos indivisibles / comensales
    costo_por_plato = costo_total / comensales
    ingreso_total = calcular_precio_venta_total(costo_total, margen, base_margen)
    precio_venta_plato = ingreso_total / comensales

    return ResultadoOrden(
        receta=receta,
        comensales=comensales,
        lineas=lineas,
        costo_total=costo_total,
        perdida_merma_total=perdida_total,
        merma_fisica_envases=merma_fisica,
        costo_por_plato=costo_por_plato,
        precio_venta_plato=precio_venta_plato,
        ingreso_total=ingreso_total,
    )


# ---------------------------------------------------------------------
# Conversión a registros para guardar en la base de datos
# ---------------------------------------------------------------------

def a_registro_orden(resultado, usuario_id):
    """Diccionario listo para insertar en la tabla 'ordenes' (números redondeados a 2 decimales)."""
    return {
        "receta_id": resultado.receta.id,
        "usuario_id": usuario_id,
        "comensales": resultado.comensales,
        "costo_total": redondear(resultado.costo_total),
        "merma_fisica_envases": redondear(resultado.merma_fisica_envases, 4),
        "perdida_merma": redondear(resultado.perdida_merma_total),
        "costo_por_plato": redondear(resultado.costo_por_plato),
        "precio_venta_plato": redondear(resultado.precio_venta_plato),
        "ingreso_total": redondear(resultado.ingreso_total),
    }


def a_registros_detalle(resultado, orden_id):
    """Lista de diccionarios para la tabla 'detalle_orden' (una fila por ingrediente)."""
    filas = []
    for l in resultado.lineas:
        filas.append({
            "orden_id": orden_id,
            "ingrediente_id": l.ingrediente.id,
            "cantidad_preparar": l.cantidad_preparar,
            "unidad_receta": l.unidad_receta,
            "envases_requeridos": l.envases,
            "capacidad_porciones": redondear(l.capacidad_porciones),
            "merma_porciones": redondear(l.merma_porciones),
            "merma_envases": redondear(l.merma_envases, 4),
            "costo_envases": redondear(l.costo_envases),
            "perdida_merma": redondear(l.perdida_merma),
        })
    return filas


# ---------------------------------------------------------------------
# Formato de texto
# ---------------------------------------------------------------------

_PLURALES = {
    "unidad": ("unidad", "unidades"),
    "paquete": ("paquete", "paquetes"),
    "kg": ("kg", "kg"),
    "litro": ("litro", "litros"),
    "empaque": ("empaque", "empaques"),
}


def texto_envases(cantidad, unidad_compra):
    """Ej: texto_envases(2, 'paquete') -> '2 paquetes'; texto_envases(1, 'kg') -> '1 kg'."""
    singular, plural = _PLURALES.get(unidad_compra, (unidad_compra, unidad_compra))
    return f"{cantidad} {singular if cantidad == 1 else plural}"


def texto_cantidad_receta(cantidad, unidad_receta):
    """Ej: (6, 'unidades') -> '6 unidades'; (1, 'unidades') -> '1 unidad'; (1, 'porciones') -> '1 porción'."""
    singular = {"unidades": "unidad", "porciones": "porción"}.get(unidad_receta, unidad_receta)
    return f"{cantidad} {singular if cantidad == 1 else unidad_receta}"


def formato_clp(valor, decimales=0):
    """Formato de pesos chilenos: 1234567.5 -> '$1.234.568' (punto como separador de miles)."""
    numero = redondear(valor, decimales)
    texto = f"{numero:,.{decimales}f}"                    # 1,234,567.50 (formato inglés)
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")   # lo paso a formato chileno
    return "$" + texto
