# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Evaluación N°3 - 26 de noviembre de 2026
# Archivo  : tests/test_calculo.py
# Ejecutar : python -m pytest -q
# ---------------------------------------------------------------------
# Pruebas del motor de cálculo con valores calculados A MANO (no con el
# mismo código), para comprobar indivisibilidad, merma, costo por plato y
# precio de venta.
# =====================================================================

import math
from fractions import Fraction

import pytest

from src.calculo import (
    calcular_orden, formato_clp, redondear, texto_envases, validar_comensales,
    a_registro_orden, a_registros_detalle,
)
from src.datos_iniciales import construir_catalogo

_, RECETAS = construir_catalogo()
POR_NOMBRE = {r.nombre: r for r in RECETAS}


def linea(resultado, ingrediente):
    return next(l for l in resultado.lineas if l.ingrediente.nombre == ingrediente)


# ---------------- Casos hechos a mano para 4 comensales ----------------

def test_arroz_con_pollo_4_comensales():
    # pollo 4*1200=4800 | arroz 1 paq=1500 | lechuga 1=1000 | aceite 1 lt=1000  -> 8300
    o = calcular_orden(POR_NOMBRE["Arroz con Pollo y Ensalada"], 4)
    assert o.costo_total == 8300
    # merma: arroz 6/10*1500=900 + lechuga 6/10*1000=600 + aceite 6/10*1000=600 = 2100 (pollo 0)
    assert o.perdida_merma_total == 2100
    assert o.costo_por_plato == Fraction(8300, 4)            # 2075
    assert o.precio_venta_plato == Fraction(8300, 4) * Fraction(5, 4)   # 2593,75
    assert o.ingreso_total == 10375
    assert linea(o, "Trutro de pollo").envases == 4
    assert linea(o, "Trutro de pollo").perdida_merma == 0
    assert linea(o, "Arroz").envases == 1
    assert linea(o, "Arroz").merma_porciones == 6
    assert linea(o, "Arroz").merma_envases == Fraction(6, 10)


def test_tortilla_4_comensales():
    # papa 1 kg=1000 | cebolla ceil(4/4)=1 -> 500 | huevo 1 emp=4500 | aceite 1000 -> 7000
    o = calcular_orden(POR_NOMBRE["Tortilla de Papas y Cebolla"], 4)
    assert o.costo_total == 7000
    # merma: huevo 8/12*4500=3000 + aceite 600 = 3600 (papa y cebolla se usan completas)
    assert o.perdida_merma_total == 3600
    assert linea(o, "Cebolla").envases == 1


def test_carne_con_arroz_y_ensalada_sin_aceite():
    # carne 1500 + arroz 1500 + lechuga 1000 + tomate 1500 = 5500 ; merma = 900+600+500 = 2000
    o = calcular_orden(POR_NOMBRE["Carne Molida con Arroz y Ensalada"], 4)
    assert o.costo_total == 5500
    assert o.perdida_merma_total == 2000


# ---------------- Indivisibilidad: redondeo hacia arriba ----------------

def test_indivisibilidad_11_comensales_arroz():
    # 11 personas / 10 por paquete = 1,1 -> 2 paquetes; sobran 9 porciones = 0,9 paquete = 1350 $
    o = calcular_orden(POR_NOMBRE["Arroz con Pollo y Ensalada"], 11)
    arroz = linea(o, "Arroz")
    assert arroz.envases == 2
    assert arroz.merma_porciones == 9
    assert arroz.perdida_merma == Fraction(9, 10) * 1500 == 1350
    assert arroz.costo_envases == 3000


def test_comensales_multiplo_exacto_no_hay_merma():
    # 20 comensales: arroz 2 paquetes exactos, aceite 2 litros exactos, pollo 20, lechuga 2
    o = calcular_orden(POR_NOMBRE["Arroz con Pollo y Ensalada"], 20)
    assert o.perdida_merma_total == 0
    assert o.costo_total == 20 * 1200 + 2 * 1500 + 2 * 1000 + 2 * 1000


def test_un_comensal():
    o = calcular_orden(POR_NOMBRE["Charquicán Simple"], 1)
    # papa 1 kg (1000), lechuga 1 (1000), cebolla 1 (500), aceite 1 lt (1000) = 3500
    assert o.costo_total == 3500
    assert o.costo_por_plato == 3500
    assert o.precio_venta_plato == Fraction(3500) * Fraction(5, 4)


def test_cantidad_a_preparar_escalada_hacia_arriba():
    # 5 comensales: papa 6*5/4 = 7,5 -> 8 unidades
    o = calcular_orden(POR_NOMBRE["Charquicán Simple"], 5)
    assert linea(o, "Papa").cantidad_preparar == 8
    # lechuga 1*5/4 = 1,25 -> 2 unidades
    assert linea(o, "Lechuga").cantidad_preparar == 2


# ---------------- Invariantes que deben cumplirse SIEMPRE ----------------

@pytest.mark.parametrize("comensales", [1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 13, 25, 40, 99, 100, 101, 500])
def test_invariantes_todas_las_recetas(comensales):
    for receta in RECETAS:
        o = calcular_orden(receta, comensales)
        assert sum(l.costo_envases for l in o.lineas) == o.costo_total
        assert sum(l.perdida_merma for l in o.lineas) == o.perdida_merma_total
        assert 0 <= o.perdida_merma_total <= o.costo_total
        for l in o.lineas:
            assert l.envases >= 1
            # se compra lo justo: nunca sobra un envase completo o más
            assert 0 <= l.merma_envases < 1
            assert l.capacidad_porciones - l.merma_porciones == comensales   # modo "comensales"
            assert l.envases == math.ceil(Fraction(comensales, l.ingrediente.personas_por_unidad))
        # costo por plato * comensales = costo total; venta = costo * 1,25
        assert o.costo_por_plato * comensales == o.costo_total
        assert o.ingreso_total == o.costo_total * Fraction(5, 4)
        assert o.precio_venta_plato * comensales == o.ingreso_total


# ---------------- Modos alternativos (supuestos configurables) ----------------

def test_modo_receta_usa_la_cantidad_de_la_receta():
    # Papa: receta 6 unidades para 4 comensales, "4 por kg" -> ceil(6/4)=2 kg (modo receta) vs 1 kg (modo comensales)
    r = POR_NOMBRE["Charquicán Simple"]
    assert linea(calcular_orden(r, 4, modo="comensales"), "Papa").envases == 1
    papa = linea(calcular_orden(r, 4, modo="receta"), "Papa")
    assert papa.envases == 2
    assert papa.merma_porciones == 2


def test_margen_sobre_venta():
    # Si el 25 % fuera margen sobre el precio: precio = costo / 0,75
    o = calcular_orden(POR_NOMBRE["Charquicán Simple"], 4, base_margen="sobre_venta")
    assert o.ingreso_total == Fraction(3500) / Fraction(3, 4)


def test_modos_invalidos():
    with pytest.raises(ValueError):
        calcular_orden(POR_NOMBRE["Charquicán Simple"], 4, modo="otro")
    with pytest.raises(ValueError):
        calcular_orden(POR_NOMBRE["Charquicán Simple"], 4, base_margen="otro")


# ---------------- Validación de entradas ----------------

@pytest.mark.parametrize("valor", [None, "", "   ", 0, -1, -50, 0.0, 2.5, "abc", float("nan"), True, 5001, [1]])
def test_comensales_invalidos(valor):
    with pytest.raises(ValueError):
        validar_comensales(valor)


@pytest.mark.parametrize("valor,esperado", [(1, 1), (25, 25), (25.0, 25), ("30", 30), (" 12 ", 12), (5000, 5000)])
def test_comensales_validos(valor, esperado):
    assert validar_comensales(valor) == esperado


def test_mensajes_distintos_para_cero_y_negativo():
    with pytest.raises(ValueError, match="cero"):
        validar_comensales(0)
    with pytest.raises(ValueError, match="negativa"):
        validar_comensales(-3)
    with pytest.raises(ValueError, match="vacío"):
        validar_comensales(None)


def test_menu_nulo():
    with pytest.raises(ValueError, match="menú"):
        calcular_orden(None, 4)


# ---------------- Registros para la BD, redondeo y formato ----------------

def test_registro_orden_y_detalle():
    o = calcular_orden(POR_NOMBRE["Arroz con Pollo y Ensalada"], 4)
    reg = a_registro_orden(o, usuario_id=7)
    assert reg["costo_total"] == 8300.0
    assert reg["perdida_merma"] == 2100.0
    assert reg["costo_por_plato"] == 2075.0
    assert reg["precio_venta_plato"] == 2593.75
    assert reg["ingreso_total"] == 10375.0
    assert reg["usuario_id"] == 7 and reg["receta_id"] == o.receta.id
    det = a_registros_detalle(o, orden_id=99)
    assert len(det) == 4 and all(d["orden_id"] == 99 for d in det)
    assert round(sum(d["perdida_merma"] for d in det), 2) == 2100.0


def test_redondeo_mitad_hacia_arriba_y_exactitud():
    assert redondear(Fraction(5, 2), 0) == 3.0                # 2,5 -> 3 (no el "redondeo bancario" de Python)
    assert redondear(Fraction(1, 3), 2) == 0.33
    assert 0.1 + 0.2 != 0.3                                    # con float hay error de representación...
    assert Fraction(1, 10) + Fraction(2, 10) == Fraction(3, 10)  # ...con Fraction no
    assert redondear(Fraction(6, 10) * 1500, 2) == 900.0


def test_formatos():
    assert formato_clp(1234567) == "$1.234.567"
    assert formato_clp(Fraction(259375, 100), 2) == "$2.593,75"
    assert texto_envases(1, "kg") == "1 kg"
    assert texto_envases(3, "kg") == "3 kg"
    assert texto_envases(2, "paquete") == "2 paquetes"
    assert texto_envases(1, "empaque") == "1 empaque"
    assert texto_envases(3, "unidad") == "3 unidades"


def test_cocina_no_recibe_campos_de_dinero():
    o = calcular_orden(POR_NOMBRE["Arroz con Pollo y Ensalada"], 10)
    for l in o.vista_cocina():
        campos = set(vars(l))
        assert campos == {"ingrediente", "envases", "unidad_compra", "cantidad_preparar", "unidad_receta"}


def test_texto_cantidad_receta():
    from src.calculo import texto_cantidad_receta
    assert texto_cantidad_receta(6, "unidades") == "6 unidades"
    assert texto_cantidad_receta(1, "unidades") == "1 unidad"
    assert texto_cantidad_receta(4, "porciones") == "4 porciones"
    assert texto_cantidad_receta(1, "porciones") == "1 porción"
