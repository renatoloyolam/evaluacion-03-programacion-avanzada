# =====================================================================
# Alumno   : Renato Loyola Muñoz
# Curso    : I CRIM Sistemas de Armas - Programación Avanzada
# Profesor : Dr. Carlos Santibáñez Rodríguez
# Evaluación N°3 - Fecha: 26 de noviembre de 2026
# Archivo  : src/estructuras.py
# Librerías: ninguna externa (todo es Python estándar)
# ---------------------------------------------------------------------
# TDAs hechos a mano (contenido 4.1, 4.3 y 4.4 de la evaluación):
#   - ListaEnlazada      -> ingredientes de una receta
#   - Pila (LIFO)        -> historial de órdenes de la sesión; recorrido del árbol
#   - Cola (FIFO)        -> recorrido en anchura (BFS) del grafo
#   - ColaPrioridad      -> ranking de mayores mermas y fusión del orden externo
#   - ArbolBinarioBusqueda -> ranking jerárquico de pérdidas por ingrediente
#   - Grafo              -> relación menú <-> ingrediente
# No usé collections.deque ni queue.PriorityQueue a propósito: la idea es
# mostrar cómo funciona cada estructura por dentro.
# =====================================================================


class Nodo:
    """Nodo simple: guarda un valor y apunta al siguiente."""

    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None


# ---------------------------------------------------------------------
# LISTA ENLAZADA
# ---------------------------------------------------------------------
class ListaEnlazada:
    """
    Lista enlazada simple con puntero a la cola, así agregar al final
    es O(1) y no hay que recorrer toda la lista cada vez.
    """

    def __init__(self, elementos=None):
        self._cabeza = None
        self._cola = None
        self._tamano = 0
        # Permite crearla directo desde otra colección: ListaEnlazada([a, b, c])
        if elementos is not None:
            for e in elementos:
                self.agregar_final(e)

    def agregar_final(self, valor):
        nodo = Nodo(valor)
        if self._cabeza is None:           # lista vacía: el nodo es cabeza y cola
            self._cabeza = nodo
            self._cola = nodo
        else:
            self._cola.siguiente = nodo
            self._cola = nodo
        self._tamano += 1

    def agregar_inicio(self, valor):
        nodo = Nodo(valor)
        nodo.siguiente = self._cabeza
        self._cabeza = nodo
        if self._cola is None:             # era una lista vacía
            self._cola = nodo
        self._tamano += 1

    def eliminar(self, valor):
        """Elimina la primera aparición de 'valor'. Devuelve True si lo encontró."""
        anterior = None
        actual = self._cabeza
        while actual is not None:
            if actual.valor == valor:
                if anterior is None:       # borrar la cabeza
                    self._cabeza = actual.siguiente
                else:
                    anterior.siguiente = actual.siguiente
                if actual is self._cola:   # borramos el último: hay que mover la cola
                    self._cola = anterior
                self._tamano -= 1
                return True
            anterior = actual
            actual = actual.siguiente
        return False

    def __iter__(self):
        # Con esto se puede usar "for x in lista" y list(lista)
        actual = self._cabeza
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente

    def __len__(self):
        return self._tamano

    def esta_vacia(self):
        return self._tamano == 0

    def a_lista(self):
        return list(self)


# ---------------------------------------------------------------------
# PILA (LIFO)
# ---------------------------------------------------------------------
class Pila:
    """Pila: el último que entra es el primero que sale."""

    def __init__(self):
        self._cabeza = None
        self._tamano = 0

    def apilar(self, valor):
        nodo = Nodo(valor)
        nodo.siguiente = self._cabeza      # el nuevo nodo queda encima
        self._cabeza = nodo
        self._tamano += 1

    def desapilar(self):
        if self._cabeza is None:
            raise IndexError("La pila está vacía")
        valor = self._cabeza.valor
        self._cabeza = self._cabeza.siguiente
        self._tamano -= 1
        return valor

    def cima(self):
        """Mira el elemento de arriba sin sacarlo."""
        if self._cabeza is None:
            raise IndexError("La pila está vacía")
        return self._cabeza.valor

    def esta_vacia(self):
        return self._tamano == 0

    def __len__(self):
        return self._tamano

    def __iter__(self):
        # Recorre desde la cima hacia el fondo (el más reciente primero)
        actual = self._cabeza
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente


# ---------------------------------------------------------------------
# COLA (FIFO)
# ---------------------------------------------------------------------
class Cola:
    """Cola: el primero que entra es el primero que sale. Encolar y desencolar son O(1)."""

    def __init__(self):
        self._frente = None
        self._final = None
        self._tamano = 0

    def encolar(self, valor):
        nodo = Nodo(valor)
        if self._final is None:
            self._frente = nodo
        else:
            self._final.siguiente = nodo
        self._final = nodo
        self._tamano += 1

    def desencolar(self):
        if self._frente is None:
            raise IndexError("La cola está vacía")
        valor = self._frente.valor
        self._frente = self._frente.siguiente
        if self._frente is None:           # se vació: también limpiamos el final
            self._final = None
        self._tamano -= 1
        return valor

    def frente(self):
        if self._frente is None:
            raise IndexError("La cola está vacía")
        return self._frente.valor

    def esta_vacia(self):
        return self._tamano == 0

    def __len__(self):
        return self._tamano

    def __iter__(self):
        actual = self._frente
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente


# ---------------------------------------------------------------------
# COLA CON PRIORIDAD (heap binario guardado en un arreglo)
# ---------------------------------------------------------------------
class ColaPrioridad:
    """
    Cola con prioridad implementada con un heap binario.

    Por defecto sale primero la prioridad MÁS BAJA (min-heap). Con
    mayor_primero=True sale primero la más alta (lo uso para sacar las
    mayores pérdidas). Si dos elementos empatan en prioridad, sale antes el
    que llegó primero (así el orden es estable y predecible).
    """

    def __init__(self, mayor_primero=False):
        self._heap = []                    # cada entrada: (prioridad, nro_llegada, valor)
        self._contador = 0
        self.mayor_primero = mayor_primero
        self.comparaciones = 0             # cuenta las comparaciones del heap (para mostrar en pantalla)

    def _antes(self, a, b):
        """True si la entrada 'a' debe salir antes que la entrada 'b'."""
        self.comparaciones += 1
        if a[0] == b[0]:
            return a[1] < b[1]             # empate: gana el que llegó antes
        if self.mayor_primero:
            return a[0] > b[0]
        return a[0] < b[0]

    def insertar(self, prioridad, valor):
        self._heap.append((prioridad, self._contador, valor))
        self._contador += 1
        self._subir(len(self._heap) - 1)

    def extraer(self):
        """Saca y devuelve (prioridad, valor) del elemento con mayor urgencia."""
        if not self._heap:
            raise IndexError("La cola de prioridad está vacía")
        raiz = self._heap[0]
        ultimo = self._heap.pop()
        if self._heap:                     # si quedan elementos, reubicamos el último
            self._heap[0] = ultimo
            self._bajar(0)
        return raiz[0], raiz[2]

    def ver_proximo(self):
        if not self._heap:
            raise IndexError("La cola de prioridad está vacía")
        return self._heap[0][0], self._heap[0][2]

    def _subir(self, i):
        # Mientras el hijo "gane" contra su padre, se intercambian
        while i > 0:
            padre = (i - 1) // 2
            if self._antes(self._heap[i], self._heap[padre]):
                self._heap[i], self._heap[padre] = self._heap[padre], self._heap[i]
                i = padre
            else:
                break

    def _bajar(self, i):
        n = len(self._heap)
        while True:
            izq, der = 2 * i + 1, 2 * i + 2
            mejor = i
            if izq < n and self._antes(self._heap[izq], self._heap[mejor]):
                mejor = izq
            if der < n and self._antes(self._heap[der], self._heap[mejor]):
                mejor = der
            if mejor == i:
                break
            self._heap[i], self._heap[mejor] = self._heap[mejor], self._heap[i]
            i = mejor

    def esta_vacia(self):
        return not self._heap

    def __len__(self):
        return len(self._heap)


# ---------------------------------------------------------------------
# ÁRBOL BINARIO DE BÚSQUEDA
# ---------------------------------------------------------------------
class _NodoArbol:
    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izq = None
        self.der = None


class ArbolBinarioBusqueda:
    """
    ABB: a la izquierda van las claves menores y a la derecha las mayores.
    Hecho con bucles (no recursión) para que no reviente con muchos datos.
    Si se repite una clave, el valor nuevo queda a la derecha (se acepta duplicados).
    """

    def __init__(self):
        self.raiz = None
        self._tamano = 0

    def insertar(self, clave, valor):
        nuevo = _NodoArbol(clave, valor)
        self._tamano += 1
        if self.raiz is None:
            self.raiz = nuevo
            return
        actual = self.raiz
        while True:
            if clave < actual.clave:
                if actual.izq is None:
                    actual.izq = nuevo
                    return
                actual = actual.izq
            else:
                if actual.der is None:
                    actual.der = nuevo
                    return
                actual = actual.der

    def buscar(self, clave):
        """Devuelve el valor asociado a la clave, o None si no está."""
        actual = self.raiz
        while actual is not None:
            if clave == actual.clave:
                return actual.valor
            actual = actual.izq if clave < actual.clave else actual.der
        return None

    def en_orden(self):
        """Recorrido inorden (menor -> mayor). Usa una Pila propia en vez de recursión."""
        resultado = []
        pila = Pila()
        actual = self.raiz
        while actual is not None or not pila.esta_vacia():
            while actual is not None:      # bajamos todo lo que podamos por la izquierda
                pila.apilar(actual)
                actual = actual.izq
            actual = pila.desapilar()
            resultado.append((actual.clave, actual.valor))
            actual = actual.der
        return resultado

    def en_orden_inverso(self):
        """Recorrido de mayor a menor (útil para rankings)."""
        resultado = self.en_orden()
        resultado.reverse()
        return resultado

    def altura(self):
        """Altura del árbol, calculada por niveles con una Cola (BFS)."""
        if self.raiz is None:
            return 0
        altura = 0
        cola = Cola()
        cola.encolar(self.raiz)
        while not cola.esta_vacia():
            for _ in range(len(cola)):     # procesa un nivel completo
                nodo = cola.desencolar()
                if nodo.izq:
                    cola.encolar(nodo.izq)
                if nodo.der:
                    cola.encolar(nodo.der)
            altura += 1
        return altura

    def __len__(self):
        return self._tamano


# ---------------------------------------------------------------------
# GRAFO NO DIRIGIDO (lista de adyacencia)
# ---------------------------------------------------------------------
class Grafo:
    """
    Grafo no dirigido con diccionario de adyacencia.
    Lo uso para relacionar menús con ingredientes: cada receta une su menú
    con los ingredientes que lleva. Así se ve qué menús comparten insumos.
    """

    def __init__(self):
        self._adyacentes = {}              # vértice -> lista de vecinos
        self._tipos = {}                   # vértice -> etiqueta ("menu" o "ingrediente")

    def agregar_vertice(self, vertice, tipo=None):
        if vertice not in self._adyacentes:
            self._adyacentes[vertice] = []
            self._tipos[vertice] = tipo
        elif tipo is not None and self._tipos[vertice] is None:
            self._tipos[vertice] = tipo       # el vértice se creó solo por una arista: le asigno el tipo ahora

    def agregar_arista(self, a, b):
        self.agregar_vertice(a)
        self.agregar_vertice(b)
        if b not in self._adyacentes[a]:   # evita aristas repetidas
            self._adyacentes[a].append(b)
            self._adyacentes[b].append(a)

    def vecinos(self, vertice):
        return list(self._adyacentes.get(vertice, []))

    def tipo(self, vertice):
        return self._tipos.get(vertice)

    def vertices(self, tipo=None):
        if tipo is None:
            return list(self._adyacentes)
        return [v for v in self._adyacentes if self._tipos[v] == tipo]

    def grado(self, vertice):
        return len(self._adyacentes.get(vertice, []))

    def bfs(self, origen):
        """
        Recorrido en anchura desde 'origen'. Devuelve {vértice: distancia}.
        En este grafo una distancia de 2 entre dos menús significa que
        comparten al menos un ingrediente.
        """
        if origen not in self._adyacentes:
            return {}
        distancias = {origen: 0}
        cola = Cola()
        cola.encolar(origen)
        while not cola.esta_vacia():
            actual = cola.desencolar()
            for vecino in self._adyacentes[actual]:
                if vecino not in distancias:
                    distancias[vecino] = distancias[actual] + 1
                    cola.encolar(vecino)
        return distancias

    def vecinos_comunes(self, a, b):
        """Vértices conectados a la vez con 'a' y con 'b' (ej: ingredientes compartidos)."""
        vb = self._adyacentes.get(b, [])
        return [v for v in self._adyacentes.get(a, []) if v in vb]
