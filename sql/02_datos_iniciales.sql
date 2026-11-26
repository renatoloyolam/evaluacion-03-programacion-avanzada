-- =====================================================================
-- Alumno   : Renato Loyola Muñoz
-- Curso    : I CRIM Sistemas de Armas - Programación Avanzada
-- Evaluación N°3 - 26 de noviembre de 2026
-- Archivo  : sql/02_datos_iniciales.sql  (GENERADO con scripts/generar_sql.py)
-- Ejecutar DESPUÉS de sql/01_esquema.sql.
-- Carga: 2 roles, 2 usuarios, 10 ingredientes, 10 recetas y sus 40 líneas de ingredientes.
-- =====================================================================

-- Roles y permisos
insert into roles (rol, descripcion, ve_costos, registra_ordenes) values
  ('cocina',        'Operador de cocina: solo ve cantidades a preparar', false, true),
  ('administrador', 'Acceso total: costos, mermas, ventas y panel gerencial', true, true);

-- Usuarios (la contraseña va como hash PBKDF2, ver README para las claves iniciales)
insert into usuarios (username, nombre_completo, password_hash, rol) values
  ('cocina', 'Operador de Cocina', 'pbkdf2_sha256$120000$df1ff431c76a01910e1be1f046b4c24b$ad7475ffc90b8eeb4f2e4fd6bb3a7f5976845202b60092581ea1ec3776deaa66', 'cocina'),
  ('admin', 'Administrador del Casino', 'pbkdf2_sha256$120000$f748922ad835bf66481c7424730cf9f7$b4070c84a5a79faeb2e379bc0e13e1bda1132dbeb9c9f8c59773aae9a707d0ed', 'administrador');

-- Los 10 ingredientes de la tabla del enunciado
insert into ingredientes (nombre, unidad_compra, costo_unitario, personas_por_unidad, descripcion_utilidad) values
  ('Cebolla', 'unidad', 500, 4, '4 personas'),
  ('Arroz', 'paquete', 1500, 10, '10 personas por paquete'),
  ('Trutro de pollo', 'unidad', 1200, 1, '1 por persona'),
  ('Carne molida', 'paquete', 1500, 4, '4 personas por paquete'),
  ('Papa', 'kg', 1000, 4, '4 personas por kg'),
  ('Tomate', 'kg', 1500, 6, '6 personas por kg'),
  ('Fideos', 'paquete', 1200, 4, '4 personas por paquete'),
  ('Lechuga', 'unidad', 1000, 10, '10 personas por lechuga'),
  ('Huevo', 'empaque', 4500, 12, '12 personas por empaque'),
  ('Aceite', 'litro', 1000, 10, '10 personas por litro');

-- Las 10 recetas (base de 4 comensales)
insert into recetas (nombre, base_comensales) values
  ('Arroz con Pollo y Ensalada', 4),
  ('Carne Molida con Papas y Arroz', 4),
  ('Tallarines con Salsa de Tomate', 4),
  ('Tortilla de Papas y Cebolla', 4),
  ('Pollo Salteado con Verduras', 4),
  ('Charquicán Simple', 4),
  ('Fideos con Huevo y Tomate', 4),
  ('Carne Molida con Arroz y Ensalada', 4),
  ('Papas Cocidas con Huevo y Lechuga', 4),
  ('Arroz Graneado con Huevo y Cebolla', 4);

-- Ingredientes de cada receta (se enlazan por nombre, así no dependen de los ids)
insert into receta_ingredientes (receta_id, ingrediente_id, cantidad, unidad_receta)
select r.id, i.id, v.cantidad, v.unidad_receta
from (values
  ('Arroz con Pollo y Ensalada', 'Trutro de pollo', 4, 'unidades'),
  ('Arroz con Pollo y Ensalada', 'Arroz', 4, 'porciones'),
  ('Arroz con Pollo y Ensalada', 'Lechuga', 1, 'unidades'),
  ('Arroz con Pollo y Ensalada', 'Aceite', 4, 'porciones'),
  ('Carne Molida con Papas y Arroz', 'Carne molida', 4, 'porciones'),
  ('Carne Molida con Papas y Arroz', 'Papa', 6, 'unidades'),
  ('Carne Molida con Papas y Arroz', 'Cebolla', 1, 'unidades'),
  ('Carne Molida con Papas y Arroz', 'Aceite', 4, 'porciones'),
  ('Tallarines con Salsa de Tomate', 'Fideos', 4, 'porciones'),
  ('Tallarines con Salsa de Tomate', 'Tomate', 4, 'unidades'),
  ('Tallarines con Salsa de Tomate', 'Cebolla', 1, 'unidades'),
  ('Tallarines con Salsa de Tomate', 'Aceite', 4, 'porciones'),
  ('Tortilla de Papas y Cebolla', 'Papa', 6, 'unidades'),
  ('Tortilla de Papas y Cebolla', 'Cebolla', 1, 'unidades'),
  ('Tortilla de Papas y Cebolla', 'Huevo', 6, 'unidades'),
  ('Tortilla de Papas y Cebolla', 'Aceite', 4, 'porciones'),
  ('Pollo Salteado con Verduras', 'Trutro de pollo', 4, 'unidades'),
  ('Pollo Salteado con Verduras', 'Tomate', 3, 'unidades'),
  ('Pollo Salteado con Verduras', 'Cebolla', 1, 'unidades'),
  ('Pollo Salteado con Verduras', 'Aceite', 4, 'porciones'),
  ('Charquicán Simple', 'Papa', 6, 'unidades'),
  ('Charquicán Simple', 'Lechuga', 1, 'unidades'),
  ('Charquicán Simple', 'Cebolla', 1, 'unidades'),
  ('Charquicán Simple', 'Aceite', 4, 'porciones'),
  ('Fideos con Huevo y Tomate', 'Fideos', 4, 'porciones'),
  ('Fideos con Huevo y Tomate', 'Huevo', 4, 'unidades'),
  ('Fideos con Huevo y Tomate', 'Tomate', 3, 'unidades'),
  ('Fideos con Huevo y Tomate', 'Aceite', 4, 'porciones'),
  ('Carne Molida con Arroz y Ensalada', 'Carne molida', 4, 'porciones'),
  ('Carne Molida con Arroz y Ensalada', 'Arroz', 4, 'porciones'),
  ('Carne Molida con Arroz y Ensalada', 'Lechuga', 1, 'unidades'),
  ('Carne Molida con Arroz y Ensalada', 'Tomate', 2, 'unidades'),
  ('Papas Cocidas con Huevo y Lechuga', 'Papa', 6, 'unidades'),
  ('Papas Cocidas con Huevo y Lechuga', 'Huevo', 4, 'unidades'),
  ('Papas Cocidas con Huevo y Lechuga', 'Lechuga', 1, 'unidades'),
  ('Papas Cocidas con Huevo y Lechuga', 'Aceite', 4, 'porciones'),
  ('Arroz Graneado con Huevo y Cebolla', 'Arroz', 4, 'porciones'),
  ('Arroz Graneado con Huevo y Cebolla', 'Huevo', 4, 'unidades'),
  ('Arroz Graneado con Huevo y Cebolla', 'Cebolla', 1, 'unidades'),
  ('Arroz Graneado con Huevo y Cebolla', 'Aceite', 4, 'porciones')
) as v(receta, ingrediente, cantidad, unidad_receta)
join recetas r      on r.nombre = v.receta
join ingredientes i on i.nombre = v.ingrediente;

-- Verificación rápida: deben salir 2 / 2 / 10 / 10 / 40
select (select count(*) from roles)               as roles,
       (select count(*) from usuarios)            as usuarios,
       (select count(*) from ingredientes)        as ingredientes,
       (select count(*) from recetas)             as recetas,
       (select count(*) from receta_ingredientes) as lineas_receta;
