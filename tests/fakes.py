# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Evaluación N°3 - 26 de noviembre de 2026
# Archivo  : tests/fakes.py
# ---------------------------------------------------------------------
# Cliente de Supabase "de mentira" que guarda las tablas en memoria y
# entiende las mismas llamadas que usa RepositorioSupabase (table, select,
# insert, delete, eq, order, range, limit, execute). Sirve para probar la
# aplicación completa sin internet ni credenciales.
# =====================================================================

import copy
import datetime as dt
from types import SimpleNamespace

from src.autenticacion import hashear_password
from src.datos_iniciales import INGREDIENTES, RECETAS


class _Consulta:
    def __init__(self, cliente, tabla):
        self.cliente = cliente
        self.tabla = tabla
        self.accion = None
        self.columnas = None
        self.payload = None
        self.filtros = []
        self.orden = None
        self.rango = None
        self.tope = None

    def select(self, columnas="*"):
        self.accion = "select"
        self.columnas = None if columnas.strip() == "*" else [c.strip() for c in columnas.split(",")]
        return self

    def insert(self, payload):
        self.accion = "insert"
        self.payload = payload
        return self

    def delete(self):
        self.accion = "delete"
        return self

    def eq(self, columna, valor):
        self.filtros.append((columna, valor))
        return self

    def order(self, columna, desc=False):
        self.orden = (columna, desc)
        return self

    def range(self, desde, hasta):
        self.rango = (desde, hasta)
        return self

    def limit(self, n):
        self.tope = n
        return self

    def execute(self):
        filas = self.cliente.tablas[self.tabla]
        if self.accion == "insert":
            nuevos = self.payload if isinstance(self.payload, list) else [self.payload]
            insertados = []
            for n in nuevos:
                fila = copy.deepcopy(n)
                fila["id"] = self.cliente.siguiente_id(self.tabla)
                if self.tabla == "ordenes":
                    fila["fecha"] = dt.datetime.now(dt.timezone.utc).isoformat()
                filas.append(fila)
                insertados.append(copy.deepcopy(fila))
            return SimpleNamespace(data=insertados)

        sel = [f for f in filas if all(f.get(c) == v for c, v in self.filtros)]
        if self.accion == "delete":
            for f in sel:
                filas.remove(f)
            if self.tabla == "ordenes":       # on delete cascade
                ids = {f["id"] for f in sel}
                self.cliente.tablas["detalle_orden"][:] = [
                    d for d in self.cliente.tablas["detalle_orden"] if d["orden_id"] not in ids]
            return SimpleNamespace(data=copy.deepcopy(sel))

        if self.orden:
            col, desc = self.orden
            sel = sorted(sel, key=lambda f: f.get(col), reverse=desc)
        if self.rango:
            sel = sel[self.rango[0]: self.rango[1] + 1]
        if self.tope is not None:
            sel = sel[: self.tope]
        if self.columnas:
            sel = [{c: f.get(c) for c in self.columnas} for f in sel]
        return SimpleNamespace(data=copy.deepcopy(sel))


class ClienteFalso:
    """Imita al cliente de supabase-py con tablas en memoria, ya cargadas con los datos iniciales."""

    def __init__(self, con_datos=True, falla_detalle=False):
        self.falla_detalle = falla_detalle
        self.tablas = {t: [] for t in (
            "roles", "usuarios", "ingredientes", "recetas", "receta_ingredientes", "ordenes", "detalle_orden")}
        self._ids = {}
        if con_datos:
            self._cargar()

    def siguiente_id(self, tabla):
        self._ids[tabla] = self._ids.get(tabla, 0) + 1
        return self._ids[tabla]

    def table(self, nombre):
        if nombre == "detalle_orden" and self.falla_detalle:
            raise RuntimeError("fallo simulado al guardar detalle")
        return _Consulta(self, nombre)

    def _cargar(self):
        self.tablas["roles"] += [
            {"rol": "cocina", "descripcion": "", "ve_costos": False, "registra_ordenes": True},
            {"rol": "administrador", "descripcion": "", "ve_costos": True, "registra_ordenes": True},
        ]
        for u, n, c, r in (("cocina", "Operador de Cocina", "Cocina2026!", "cocina"),
                           ("admin", "Administrador", "Admin2026!", "administrador")):
            self.tablas["usuarios"].append({
                "id": self.siguiente_id("usuarios"), "username": u, "nombre_completo": n,
                "password_hash": hashear_password(c, iteraciones=1000), "rol": r, "activo": True})
        for nombre, unidad, costo, personas, desc in INGREDIENTES:
            self.tablas["ingredientes"].append({
                "id": self.siguiente_id("ingredientes"), "nombre": nombre, "unidad_compra": unidad,
                "costo_unitario": costo, "personas_por_unidad": personas, "descripcion_utilidad": desc})
        ids_ing = {f["nombre"]: f["id"] for f in self.tablas["ingredientes"]}
        for nombre, base, items in RECETAS:
            rid = self.siguiente_id("recetas")
            self.tablas["recetas"].append({"id": rid, "nombre": nombre, "base_comensales": base})
            for ing, cant, unidad in items:
                self.tablas["receta_ingredientes"].append({
                    "id": self.siguiente_id("receta_ingredientes"), "receta_id": rid,
                    "ingrediente_id": ids_ing[ing], "cantidad": cant, "unidad_receta": unidad})
