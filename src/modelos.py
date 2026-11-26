# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/modelos.py
# Librerías: dataclasses, fractions (estándar); estructuras.py y busqueda.py (propios)
# ---------------------------------------------------------------------
# Clases del dominio (contenido 4.2): Ingrediente, Receta, Usuario y los
# resultados del cálculo de una orden. Acá solo hay datos y comportamiento
# simple; las cuentas están en calculo.py y las consultas en base_datos.py.
#
# Decisión importante: el resultado que ve el perfil COCINA es una clase
# aparte (LineaCocina) que ni siquiera tiene campos de costo. Así, aunque
# alguien se equivoque en la interfaz, es imposible que cocina vea plata.
# =====================================================================

from dataclasses import dataclass, field
from fractions import Fraction

from src.busqueda import buscar_por_texto
from src.estructuras import ListaEnlazada


def a_fraccion(valor):
    """
    Convierte un número de la base de datos (int, float o str) a Fraction.
    Paso por str para que 0.1 sea exactamente 1/10 y no 0.1000000000000000055...
    """
    if isinstance(valor, Fraction):
        return valor
    return Fraction(str(valor))


# ---------------------------------------------------------------------
# Ingredientes y recetas
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Ingrediente:
    """
    Un insumo del catálogo. 'personas_por_unidad' es la columna "Utilidad" de
    la tabla del enunciado (cuántas personas rinde un envase completo).
    'unidad_compra' es cómo se compra: unidad, paquete, kg, litro o empaque.
    """
    id: int
    nombre: str
    unidad_compra: str
    costo_unitario: Fraction
    personas_por_unidad: int

    @classmethod
    def desde_fila(cls, fila):
        """Arma el objeto a partir de una fila (diccionario) de Supabase."""
        return cls(
            id=int(fila["id"]),
            nombre=fila["nombre"],
            unidad_compra=fila["unidad_compra"],
            costo_unitario=a_fraccion(fila["costo_unitario"]),
            personas_por_unidad=int(fila["personas_por_unidad"]),
        )


@dataclass(frozen=True)
class ItemReceta:
    """Una línea de la receta: cuánto lleva de un ingrediente para la base de comensales."""
    ingrediente: Ingrediente
    cantidad: Fraction          # cantidad para la base (ej: 6 papas para 4 comensales)
    unidad_receta: str          # 'unidades' o 'porciones'


class Receta:
    """
    Receta de un menú. Los ítems se guardan en una ListaEnlazada (TDA propio).
    'base_comensales' es para cuántos comensales está pensada la receta (4).
    """

    def __init__(self, id, nombre, base_comensales, items=None):
        self.id = id
        self.nombre = nombre
        self.base_comensales = int(base_comensales)
        self.items = ListaEnlazada(items)

    def agregar_item(self, item):
        self.items.agregar_final(item)

    def buscar_item(self, nombre_ingrediente):
        """Busca un ingrediente dentro de la receta (búsqueda secuencial)."""
        return buscar_por_texto(self.items, lambda it: it.ingrediente.nombre, nombre_ingrediente)

    def __repr__(self):
        return f"Receta({self.nombre!r}, base={self.base_comensales}, ingredientes={len(self.items)})"


# ---------------------------------------------------------------------
# Usuarios y permisos
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Usuario:
    """
    Usuario ya autenticado. No guarda la contraseña ni el hash.
    Los permisos vienen de la tabla 'roles' de la base de datos.
    """
    id: int
    username: str
    nombre_completo: str
    rol: str
    ve_costos: bool = False
    registra_ordenes: bool = False


# ---------------------------------------------------------------------
# Resultado del cálculo de una orden
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class LineaCocina:
    """
    Lo único que ve el perfil cocina por cada ingrediente: qué es y cuántos
    envases completos tiene que sacar de bodega. Sin costos, sin mermas.
    (Como los productos son indivisibles, la cantidad requerida son los
    envases/unidades completas que se calcularon con math.ceil.)
    """
    ingrediente: str
    envases: int                # envases completos que hay que usar
    unidad_compra: str          # 'paquete', 'kg', 'litro', 'unidad', 'empaque'


@dataclass(frozen=True)
class LineaInsumo:
    """Detalle completo (con plata y merma) de un ingrediente en una orden. Solo para administrador."""
    ingrediente: Ingrediente
    cantidad_preparar: int          # cantidad de la receta escalada (referencial; se guarda en la BD)
    unidad_receta: str
    envases: int
    capacidad_porciones: Fraction   # envases * personas_por_unidad
    merma_porciones: Fraction       # lo que sobra de esa capacidad
    merma_envases: Fraction         # lo mismo pero expresado en fracción de envase
    costo_envases: Fraction         # envases * costo unitario (se paga el envase entero)
    perdida_merma: Fraction         # valor en pesos de la parte que se bota


@dataclass
class ResultadoOrden:
    """Resultado completo del motor de cálculo para un servicio."""
    receta: Receta
    comensales: int
    lineas: list = field(default_factory=list)      # lista de LineaInsumo
    costo_total: Fraction = Fraction(0)
    perdida_merma_total: Fraction = Fraction(0)
    merma_fisica_envases: Fraction = Fraction(0)
    costo_por_plato: Fraction = Fraction(0)
    precio_venta_plato: Fraction = Fraction(0)
    ingreso_total: Fraction = Fraction(0)

    @property
    def costo_utilizado(self):
        """Parte del costo que sí se aprovechó (costo total menos lo perdido)."""
        return self.costo_total - self.perdida_merma_total

    @property
    def utilidad_proyectada(self):
        return self.ingreso_total - self.costo_total

    @property
    def porcentaje_merma(self):
        """Pérdida por merma como % del costo total de la orden."""
        if self.costo_total == 0:
            return Fraction(0)
        return self.perdida_merma_total / self.costo_total * 100

    def vista_cocina(self):
        """Lista de LineaCocina: la ÚNICA información que se le muestra a cocina."""
        return [
            LineaCocina(
                ingrediente=l.ingrediente.nombre,
                envases=l.envases,
                unidad_compra=l.ingrediente.unidad_compra,
            )
            for l in self.lineas
        ]
