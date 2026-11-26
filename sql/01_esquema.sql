-- =====================================================================
-- Alumno   : Renato Loyola Muñoz
-- Curso    : I CRIM Sistemas de Armas - Programación Avanzada
-- Profesor : Dr. Carlos Santibáñez Rodríguez
-- Evaluación N°3 - 26 de noviembre de 2026
-- Archivo  : sql/01_esquema.sql
-- ---------------------------------------------------------------------
-- Esquema relacional (Actividad 1). Ejecutar en Supabase:
--   SQL Editor -> New query -> pegar TODO este archivo -> Run.
-- Después ejecutar sql/02_datos_iniciales.sql.
--
-- OJO: las primeras líneas borran las tablas si ya existen (para poder repetir
-- el script). Supabase avisa que la consulta es "destructiva": es normal.
--
-- Diagrama (resumen):
--   roles 1---N usuarios 1---N ordenes N---1 recetas 1---N receta_ingredientes N---1 ingredientes
--                                 |1
--                                 N
--                            detalle_orden N---1 ingredientes
-- =====================================================================

drop table if exists detalle_orden        cascade;
drop table if exists ordenes              cascade;
drop table if exists receta_ingredientes  cascade;
drop table if exists recetas              cascade;
drop table if exists ingredientes         cascade;
drop table if exists usuarios             cascade;
drop table if exists roles                cascade;

-- ---------------------------------------------------------------------
-- 1) PERFILES Y USUARIOS (control de acceso)
-- ---------------------------------------------------------------------
-- Cada rol guarda sus permisos. La app lee estas columnas para decidir
-- qué pantallas muestra: 'cocina' no ve costos; 'administrador' ve todo.
create table roles (
    rol               text primary key,
    descripcion       text    not null,
    ve_costos         boolean not null default false,   -- puede ver costos, mermas y ventas
    registra_ordenes  boolean not null default false    -- puede ingresar servicios
);

create table usuarios (
    id               bigint generated always as identity primary key,
    username         text    not null unique,
    nombre_completo  text    not null,
    password_hash    text    not null,                  -- hash PBKDF2, nunca la clave en texto plano
    rol              text    not null references roles(rol),
    activo           boolean not null default true,
    creado_en        timestamptz not null default now()
);

-- ---------------------------------------------------------------------
-- 2) CATÁLOGO: ingredientes y recetas
-- ---------------------------------------------------------------------
create table ingredientes (
    id                    bigint generated always as identity primary key,
    nombre                text          not null unique,
    unidad_compra         text          not null
                          check (unidad_compra in ('unidad','paquete','kg','litro','empaque')),
    costo_unitario        numeric(12,2) not null check (costo_unitario > 0),   -- $ por unidad de compra
    personas_por_unidad   integer       not null check (personas_por_unidad > 0), -- "Utilidad" de la tabla
    descripcion_utilidad  text                                                   -- texto original del enunciado
);

create table recetas (
    id               bigint generated always as identity primary key,
    nombre           text    not null unique,
    base_comensales  integer not null default 4 check (base_comensales > 0)
);

-- Tabla puente (relación N a N): qué lleva cada receta y cuánto
create table receta_ingredientes (
    id              bigint generated always as identity primary key,
    receta_id       bigint        not null references recetas(id) on delete cascade,
    ingrediente_id  bigint        not null references ingredientes(id) on delete restrict,
    cantidad        numeric(10,2) not null check (cantidad > 0),
    unidad_receta   text          not null check (unidad_receta in ('unidades','porciones')),
    unique (receta_id, ingrediente_id)                  -- un ingrediente una sola vez por receta
);

-- ---------------------------------------------------------------------
-- 3) ÓRDENES Y MERMAS (persistencia de cada servicio)
-- ---------------------------------------------------------------------
create table ordenes (
    id                    bigint generated always as identity primary key,
    receta_id             bigint        not null references recetas(id)   on delete restrict,
    usuario_id            bigint        not null references usuarios(id)  on delete restrict,
    comensales            integer       not null check (comensales > 0),
    fecha                 timestamptz   not null default now(),
    costo_total           numeric(14,2) not null check (costo_total >= 0),
    merma_fisica_envases  numeric(12,4) not null check (merma_fisica_envases >= 0),
    perdida_merma         numeric(14,2) not null check (perdida_merma >= 0),
    costo_por_plato       numeric(14,2) not null check (costo_por_plato >= 0),
    precio_venta_plato    numeric(14,2) not null check (precio_venta_plato >= 0),
    ingreso_total         numeric(14,2) not null check (ingreso_total >= 0)
);

-- Una fila por ingrediente de cada orden (insumos calculados, merma y costos)
create table detalle_orden (
    id                    bigint generated always as identity primary key,
    orden_id              bigint        not null references ordenes(id)      on delete cascade,
    ingrediente_id        bigint        not null references ingredientes(id) on delete restrict,
    cantidad_preparar     integer       not null check (cantidad_preparar > 0),
    unidad_receta         text          not null,
    envases_requeridos    integer       not null check (envases_requeridos > 0),
    capacidad_porciones   numeric(12,2) not null,
    merma_porciones       numeric(12,2) not null check (merma_porciones >= 0),
    merma_envases         numeric(12,4) not null check (merma_envases >= 0),
    costo_envases         numeric(14,2) not null check (costo_envases >= 0),
    perdida_merma         numeric(14,2) not null check (perdida_merma >= 0)
);

-- Índices para las consultas del panel (filtrar por menú y por orden)
create index idx_ordenes_receta  on ordenes(receta_id);
create index idx_detalle_orden   on detalle_orden(orden_id);

-- ---------------------------------------------------------------------
-- 4) SEGURIDAD: Row Level Security
-- ---------------------------------------------------------------------
-- Se activa RLS sin políticas: la clave pública (anon/publishable) NO puede
-- leer nada, ni siquiera los hashes de usuarios. La app usa la clave SECRETA
-- (sb_secret_...) desde el servidor (st.secrets), que sí puede operar.
alter table roles               enable row level security;
alter table usuarios            enable row level security;
alter table ingredientes        enable row level security;
alter table recetas             enable row level security;
alter table receta_ingredientes enable row level security;
alter table ordenes             enable row level security;
alter table detalle_orden       enable row level security;
