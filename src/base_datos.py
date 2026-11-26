# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/base_datos.py
# Librerías: supabase (create_client); config.py, modelos.py, calculo.py (propios)
# ---------------------------------------------------------------------
# Toda la comunicación con Supabase pasa por esta clase (Repositorio).
# La interfaz nunca llama a supabase directamente: así las consultas quedan
# separadas de la parte visual y del cálculo, y se pueden reemplazar en
# los tests por un repositorio falso en memoria.
# =====================================================================

from src.calculo import a_registro_orden, a_registros_detalle
from src.config import obtener_credenciales_supabase
from src.modelos import Ingrediente, ItemReceta, Receta, a_fraccion

TAMANO_PAGINA = 1000       # Supabase devuelve máximo 1000 filas por consulta; se pide por páginas


class ErrorBaseDatos(Exception):
    """Error al hablar con Supabase (con un mensaje entendible para mostrar)."""


def crear_cliente_supabase():
    """Crea el cliente usando las credenciales de st.secrets / variables de entorno."""
    from supabase import create_client      # import local: los tests no necesitan la librería
    url, key = obtener_credenciales_supabase()
    return create_client(url, key)


class RepositorioSupabase:
    def __init__(self, cliente):
        self.db = cliente

    # ------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------
    def _traer_todo(self, tabla, columnas="*", orden=None):
        """Trae todas las filas de una tabla pidiendo de a 1000 (paginación)."""
        filas = []
        desde = 0
        while True:
            consulta = self.db.table(tabla).select(columnas)
            if orden:
                consulta = consulta.order(orden)
            pagina = consulta.range(desde, desde + TAMANO_PAGINA - 1).execute().data
            filas.extend(pagina)
            if len(pagina) < TAMANO_PAGINA:
                break
            desde += TAMANO_PAGINA
        return filas

    # ------------------------------------------------------------
    # Catálogo (ingredientes y recetas)
    # ------------------------------------------------------------
    def obtener_recetas(self):
        """
        Lee ingredientes, recetas y la tabla puente y arma los objetos Receta.
        Hago el 'join' en Python (3 consultas simples) en vez de usar relaciones
        anidadas de PostgREST, que son más difíciles de depurar.
        """
        ingredientes = {f["id"]: Ingrediente.desde_fila(f) for f in self._traer_todo("ingredientes", orden="id")}
        recetas = {}
        for f in self._traer_todo("recetas", orden="id"):
            recetas[f["id"]] = Receta(f["id"], f["nombre"], f["base_comensales"])
        for f in self._traer_todo("receta_ingredientes", orden="id"):
            receta = recetas.get(f["receta_id"])
            ingrediente = ingredientes.get(f["ingrediente_id"])
            if receta is None or ingrediente is None:
                continue
            receta.agregar_item(ItemReceta(ingrediente, a_fraccion(f["cantidad"]), f["unidad_receta"]))
        return list(recetas.values())

    def obtener_ingredientes(self):
        return [Ingrediente.desde_fila(f) for f in self._traer_todo("ingredientes", orden="id")]

    # ------------------------------------------------------------
    # Usuarios y roles
    # ------------------------------------------------------------
    def obtener_usuarios(self):
        """Filas de usuarios (incluye el hash: solo se usa dentro de autenticar())."""
        return self._traer_todo("usuarios", orden="id")

    def obtener_roles(self):
        return self._traer_todo("roles")

    # ------------------------------------------------------------
    # Órdenes
    # ------------------------------------------------------------
    def guardar_orden(self, resultado, usuario_id):
        """
        Guarda la orden y su detalle. PostgREST no hace transacciones entre dos
        inserts, así que si falla el detalle borro la orden recién creada
        para no dejar registros a medias. Devuelve el id de la orden.
        """
        try:
            respuesta = self.db.table("ordenes").insert(a_registro_orden(resultado, usuario_id)).execute()
            orden_id = respuesta.data[0]["id"]
        except Exception as e:
            raise ErrorBaseDatos(f"No se pudo guardar la orden en Supabase: {e}") from e

        try:
            self.db.table("detalle_orden").insert(a_registros_detalle(resultado, orden_id)).execute()
        except Exception as e:
            try:
                self.db.table("ordenes").delete().eq("id", orden_id).execute()
            except Exception:
                pass
            raise ErrorBaseDatos(f"No se pudo guardar el detalle de la orden: {e}") from e
        return orden_id

    def obtener_ordenes_cocina(self, limite=30):
        """
        Historial para el perfil cocina: pido SOLO columnas sin plata
        (id, fecha, menú, comensales). Los costos ni siquiera viajan a la app.
        """
        filas = (
            self.db.table("ordenes")
            .select("id, fecha, comensales, receta_id")
            .order("id", desc=True)
            .limit(limite)
            .execute()
            .data
        )
        return filas

    def obtener_ordenes(self):
        """Todas las órdenes con el nombre del menú (solo administrador)."""
        recetas = {f["id"]: f["nombre"] for f in self._traer_todo("recetas")}
        ordenes = self._traer_todo("ordenes", orden="id")
        for o in ordenes:
            o["menu"] = recetas.get(o["receta_id"], f"Menú #{o['receta_id']}")
        return ordenes

    def obtener_detalle_ordenes(self):
        """Todas las líneas de detalle con el nombre del ingrediente (solo administrador)."""
        ingredientes = {f["id"]: f for f in self._traer_todo("ingredientes")}
        detalle = self._traer_todo("detalle_orden", orden="id")
        for d in detalle:
            ing = ingredientes.get(d["ingrediente_id"])
            d["ingrediente"] = ing["nombre"] if ing else f"Ingrediente #{d['ingrediente_id']}"
            d["unidad_compra"] = ing["unidad_compra"] if ing else ""
        return detalle

    def contar_registros_base(self):
        """Cantidad de filas en las tablas del catálogo; sirve para el diagnóstico inicial."""
        return {
            "ingredientes": len(self._traer_todo("ingredientes", "id")),
            "recetas": len(self._traer_todo("recetas", "id")),
            "usuarios": len(self._traer_todo("usuarios", "id")),
        }
