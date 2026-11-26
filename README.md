# Control de Alimentos y Mermas — Evaluación N°3

**Alumno:** Renato Loyola Muñoz  
**Curso:** I CRIM Sistemas de Armas · Programación Avanzada  
**Profesor:** Dr. Carlos Santibáñez Rodríguez  
**Fecha:** 26 de noviembre de 2026  
**Tecnologías:** Python · Streamlit · Supabase (PostgreSQL) · pandas · altair

Sistema web con dos perfiles. **Cocina** ingresa el menú y la cantidad de comensales y recibe la orden de preparación
(solo cantidades). **Administrador** ve todo: costos, mermas, ventas, historial filtrable y análisis de pérdidas.
Cada servicio queda guardado en Supabase con sus cálculos completos.

## 1. Cómo ejecutarlo

```bash
# 1) Entorno virtual e instalación
python -m venv venv
venv\Scripts\activate          # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt

# 2) Base de datos: en Supabase -> SQL Editor, ejecutar en este orden
#      sql/01_esquema.sql
#      sql/02_datos_iniciales.sql      (debe mostrar 2 / 2 / 10 / 10 / 40)

# 3) Credenciales: copiar .streamlit/secrets.toml.example a .streamlit/secrets.toml
#    y poner la URL del proyecto y la Secret key (sb_secret_...)

# 4) Ejecutar
streamlit run app.py
```

**Usuarios iniciales** (la clave se guarda como hash PBKDF2, no en texto plano):

| Usuario | Contraseña | Perfil |
|---|---|---|
| `cocina` | `Cocina2026!` | cocina |
| `admin` | `Admin2026!` | administrador |

Para cambiar una contraseña: `python scripts/generar_hash.py cocina` y pegar el `update` que entrega en el SQL Editor.

**Pruebas automáticas:** `pip install -r requirements-dev.txt` y luego `python -m pytest -q`
(133 pruebas: motor de cálculo, estructuras de datos, ordenamientos, autenticación, repositorio y la aplicación completa con una base simulada).

## 2. Estructura del proyecto

```
app.py                    login + navegación por rol (punto de entrada)
src/
  config.py               constantes del negocio y lectura de credenciales (st.secrets / variables de entorno)
  modelos.py              clases: Ingrediente, Receta, ItemReceta, Usuario, LineaCocina, LineaInsumo, ResultadoOrden
  estructuras.py          TDAs: ListaEnlazada, Pila, Cola, ColaPrioridad, ArbolBinarioBusqueda, Grafo
  calculo.py              motor de cálculo (indivisibilidad, merma, costo por plato, precio de venta)
  ordenamiento.py         burbuja, inserción, quicksort, merge sort + merge sort EXTERNO con archivos temporales
  busqueda.py             búsqueda secuencial
  autenticacion.py        hash PBKDF2, validación de acceso, permisos por rol
  base_datos.py           todas las consultas a Supabase (RepositorioSupabase)
  analisis.py             KPIs, resúmenes, rankings, filtros y grafo para el panel gerencial
  servicios.py            une cálculo + guardado (registrar_orden)
  datos_iniciales.py      los 10 ingredientes y 10 recetas del enunciado
  vistas/                 pantallas: login.py, cocina.py, admin.py, componentes.py
sql/                      01_esquema.sql, 02_datos_iniciales.sql (generado)
scripts/                  generar_sql.py, generar_hash.py
tests/                    pruebas automáticas
.streamlit/secrets.toml.example
```

La separación pedida en la Actividad 5: **lógica de cálculo** (`calculo.py`), **consultas a la base de datos** (`base_datos.py`)
e **interfaz** (`vistas/` y `app.py`). Las funciones de cálculo no importan Streamlit ni Supabase.

## 3. Modelo de datos (Actividad 1)

```
roles 1──N usuarios 1──N ordenes N──1 recetas 1──N receta_ingredientes N──1 ingredientes
                              1
                              N
                        detalle_orden N──1 ingredientes
```

| Tabla | Para qué sirve |
|---|---|
| `ingredientes` | 10 insumos: costo por unidad de compra, unidad (kg, paquete, litro…) y personas que rinde ("Utilidad") |
| `recetas` | 10 menús con su base de comensales (4) |
| `receta_ingredientes` | tabla puente: qué lleva cada receta y cuánto (40 líneas) |
| `roles` | permisos por perfil (`ve_costos`, `registra_ordenes`) |
| `usuarios` | credenciales (hash) y rol, con llave foránea a `roles` |
| `ordenes` | cada servicio: menú, comensales, usuario, fecha, costo total, merma física, pérdida, costo por plato, precio de venta e ingreso |
| `detalle_orden` | una fila por ingrediente de cada orden: envases, capacidad, merma (porciones y envases), costo y pérdida |

Hay llaves foráneas, `CHECK` (valores positivos, unidades válidas), `UNIQUE` (no repetir ingrediente en una receta) e índices.
Todas las tablas tienen **Row Level Security** activado sin políticas: solo se puede operar con la clave secreta desde el servidor.

## 4. Motor de cálculo (Actividad 2)

Para cada ingrediente de la receta elegida y `n` comensales:

1. `envases = math.ceil(n / personas_por_unidad)` → los productos son **indivisibles**, se compra el envase completo.
2. `capacidad = envases × personas_por_unidad`
3. `merma física = capacidad − n` (porciones), o `merma / personas_por_unidad` expresada en fracción de envase.
4. `costo = envases × costo_unitario`
5. `pérdida por merma = (merma / personas_por_unidad) × costo_unitario`

Totales de la orden:

* `costo por plato = costo total / comensales`
* `valor de venta por plato = costo por plato × 1,25` (ganancia del 25 %)
* `ingreso proyectado = costo total × 1,25`

Se usa `fractions.Fraction` para que los totales cuadren exactamente (el costo por plato × comensales es igual al costo total)
y se redondea a 2 decimales solo al mostrar o guardar.

### Supuestos tomados (declarados, y cada uno se cambia en una línea de `src/config.py`)

| Tema | Supuesto | Alternativa |
|---|---|---|
| Cuántos envases comprar | La columna **Utilidad** de la tabla manda: `ceil(comensales / personas por envase)` (`MODO_DEMANDA = "comensales"`) | `"receta"`: usa la cantidad de la receta escalada (6 papas para 4 → `ceil(6/4)`) |
| Ganancia del 25 % | **Sobre el costo**: precio = costo × 1,25 (`BASE_MARGEN = "sobre_costo"`) | `"sobre_venta"`: precio = costo / 0,75 |
| Una orden | Un menú por servicio | — |
| Merma | Todo lo que sobra del envase se bota (no se guarda) | — |

Observaciones de los datos del enunciado, que se respetaron tal cual: la tabla dice "Tuto de pollo" (se escribió *Trutro de pollo*);
*Carne Molida con Papas y Arroz* no lista arroz entre sus ingredientes; *Charquicán Simple* no lleva carne;
*Carne Molida con Arroz y Ensalada* no lleva aceite.

### Valores de referencia para 4 comensales

| Menú | Costo total ($) | Pérdida por merma ($) | Costo por plato ($) | Valor de venta por plato ($) |
|---|---:|---:|---:|---:|
| Arroz con Pollo y Ensalada | 8.300 | 2.100 | 2.075,00 | 2.593,75 |
| Carne Molida con Papas y Arroz | 4.000 | 600 | 1.000,00 | 1.250,00 |
| Tallarines con Salsa de Tomate | 4.200 | 1.100 | 1.050,00 | 1.312,50 |
| Tortilla de Papas y Cebolla | 7.000 | 3.600 | 1.750,00 | 2.187,50 |
| Pollo Salteado con Verduras | 7.800 | 1.100 | 1.950,00 | 2.437,50 |
| Charquicán Simple | 3.500 | 1.200 | 875,00 | 1.093,75 |
| Fideos con Huevo y Tomate | 8.200 | 4.100 | 2.050,00 | 2.562,50 |
| Carne Molida con Arroz y Ensalada | 5.500 | 2.000 | 1.375,00 | 1.718,75 |
| Papas Cocidas con Huevo y Lechuga | 7.500 | 4.200 | 1.875,00 | 2.343,75 |
| Arroz Graneado con Huevo y Cebolla | 7.500 | 4.500 | 1.875,00 | 2.343,75 |

## 5. Perfiles y seguridad (Actividad 3)

* El rol sale de la base de datos (tabla `usuarios` → `roles`), no de lo que escriba el usuario.
* **Cocina** solo ve: menú, comensales e ingredientes con la cantidad requerida. Esto está garantizado por diseño:
  la clase `LineaCocina` no tiene campos de dinero y la consulta del historial de cocina ni siquiera pide columnas con costos.
* **Administrador** accede al panel gerencial y a la vista completa de órdenes. Cada pantalla gerencial llama a `exigir_costos()`
  como segunda barrera.
* Validaciones del formulario: menú obligatorio y comensales no nulo, ni cero, ni negativo, ni decimal, con un máximo de 5000.
* Contraseñas con PBKDF2-SHA256 + sal aleatoria, comparación en tiempo constante, mensaje único de error y bloqueo
  de 30 s tras 5 intentos fallidos.
* Las claves de Supabase están en `st.secrets` (`.streamlit/secrets.toml`, ignorado por git) o variables de entorno; no hay claves en el código.

## 6. Panel gerencial (Actividad 4)

1. **Resumen ejecutivo:** servicios realizados, costo total acumulado, pérdida total por merma, ingresos proyectados,
   utilidad, % de merma y las 5 órdenes con mayor pérdida.
2. **Historial de preparaciones:** tabla con filtro por menú, orden por columna (mayor/menor) y elección del algoritmo
   (merge sort, quicksort, inserción, burbuja o merge externo por bloques), con el desglose de insumos de cada orden.
3. **Análisis de mermas:** menú e ingrediente que más pérdida generan, gráficos de barras ordenados, tablas con % de merma sobre el costo
   y un grafo menú–ingrediente que muestra qué menús comparten insumos.

## 7. Contenidos del curso aplicados

| Contenido | Dónde se usa |
|---|---|
| 4.1 Lista | `ListaEnlazada`: ingredientes de cada `Receta` |
| 4.1 Pila | `Pila`: órdenes de la sesión de cocina (la más reciente arriba); recorrido inorden del árbol |
| 4.1 Cola | `Cola`: recorrido en anchura (BFS) del grafo y altura del árbol |
| 4.1 Cola con prioridad | `ColaPrioridad` (heap): top 5 de mayores pérdidas y fusión del ordenamiento externo |
| 4.2 Clases / TDA | `modelos.py`, `estructuras.py` |
| 4.3 Árbol binario | `ArbolBinarioBusqueda`: ranking jerárquico de pérdida por ingrediente |
| 4.4 Grafo | `Grafo`: relación menú–ingrediente, menús que comparten insumos |
| 5.1 Ordenamiento interno | burbuja, inserción, quicksort (con pila propia) y merge sort |
| 5.2 Ordenamiento externo | `ordenamiento_externo`: bloques ordenados en archivos temporales + fusión de K vías |
| 5.3 Búsqueda secuencial | login, catálogo de menús/ingredientes y filtros del historial |

## 8. Cobertura de la rúbrica

| Criterio (puntos) | Dónde se cumple |
|---|---|
| 1. Base de datos (10) | `sql/01_esquema.sql`, `sql/02_datos_iniciales.sql` (10 ingredientes, 10 recetas, roles y usuarios, tablas de órdenes y mermas) |
| 2. Motor de cálculo (15) | `src/calculo.py` + `tests/test_calculo.py` |
| 3. Interfaz cocina (15) | `src/vistas/cocina.py`, `componentes.py`, `login.py` |
| 4. Panel administrador (15) | `src/vistas/admin.py`, `src/analisis.py` |
| 5. Código y seguridad (5) | encabezado en cada archivo, módulos separados, `st.secrets`, `requirements.txt`, `.gitignore` |
