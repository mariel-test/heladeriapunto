-- ============================================
-- FRÍO & PUNTO — seed.sql
-- Crea tablas y carga datos iniciales
-- PostgreSQL 16+
-- ============================================

-- Limpieza por si se re-ejecuta
--DROP TABLE IF EXISTS pedidos;
--DROP TABLE IF EXISTS productos;
--DROP TABLE IF EXISTS sabores;

-- ============================================
-- TABLAS
-- ============================================

CREATE TABLE IF NOT EXISTS sabores (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    categoria   VARCHAR(20)  NOT NULL CHECK (categoria IN ('crema', 'agua')),
    sin_tacc    BOOLEAN      NOT NULL DEFAULT false,
    vegano      BOOLEAN      NOT NULL DEFAULT false,
    alergenos   TEXT[]       NOT NULL DEFAULT '{}'  -- array de strings
);

CREATE TABLE IF NOT EXISTS productos (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    sabores_max INT          NOT NULL CHECK (sabores_max > 0),
    precio      NUMERIC(10,2) NOT NULL CHECK (precio > 0)
);

CREATE TABLE IF NOT EXISTS pedidos(
    id                 SERIAL PRIMARY KEY,
    producto_id        INT          NOT NULL REFERENCES productos(id),
    sabores_elegidos   JSONB        NOT NULL DEFAULT '[]',  -- [{id, nombre}]
    total              NUMERIC(10,2) NOT NULL,
    estado             VARCHAR(20)  NOT NULL DEFAULT 'pendiente'
                                    CHECK (estado IN ('pendiente', 'confirmado', 'cancelado')),
    created_at         TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- Solo inserta si la tabla está vacía
INSERT INTO sabores (nombre, categoria, sin_tacc, vegano, alergenos)
SELECT * FROM (VALUES
    ('Dulce de leche',   'crema', true,  false, ARRAY['lactosa']),
    ('Chocolate',        'crema', true,  false, ARRAY['lactosa']),
    ('Crema americana',  'crema', true,  false, ARRAY['lactosa']),
    ('Coco',             'crema', true,  false, ARRAY['lactosa']),
    ('Brownie con chips','crema', false, false, ARRAY['lactosa', 'gluten', 'maní']),
    ('Tramontana',       'crema', false, false, ARRAY['lactosa', 'gluten']),
    ('Frutilla',         'agua',  true,  true,  ARRAY[]::TEXT[]),
    ('Limón',            'agua',  true,  true,  ARRAY[]::TEXT[]),
    ('Maracuyá',         'agua',  true,  true,  ARRAY[]::TEXT[]),
    ('Menta',            'agua',  true,  true,  ARRAY[]::TEXT[])
) AS datos(nombre, categoria, sin_tacc, vegano, alergenos)
WHERE NOT EXISTS (SELECT 1 FROM sabores);

INSERT INTO productos (nombre, sabores_max, precio)
SELECT * FROM (VALUES
    ('Pote 1/4 kg',      1, 2800.00),
    ('Pote 1/2 kg',      2, 4500.00),
    ('Pote 1 kg',        4, 7800.00),
    ('Cucurucho simple', 1, 1200.00),
    ('Combo familiar',   4, 9500.00)
) AS datos(nombre, sabores_max, precio)
WHERE NOT EXISTS (SELECT 1 FROM productos);