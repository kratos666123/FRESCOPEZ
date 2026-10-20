-- ============================================================
-- FrescoPez SAS — Manual DB patch (run ONCE in MySQL/MariaDB)
-- Run this if you get 500 errors on /entregas or /pedidos
-- ============================================================

-- 1. Rename orders.fecha (Date) → fecha_hora (DateTime)
ALTER TABLE orders ADD COLUMN fecha_hora DATETIME NULL AFTER documento_cliente;
UPDATE orders SET fecha_hora = CAST(fecha AS DATETIME) WHERE fecha IS NOT NULL;
ALTER TABLE orders MODIFY COLUMN fecha_hora DATETIME NOT NULL;
ALTER TABLE orders DROP COLUMN fecha;

-- 2. Change id_domiciliario FK in orders from RESTRICT to SET NULL
ALTER TABLE orders MODIFY COLUMN id_domiciliario INT NULL;

-- 3. Add nombre_domiciliario snapshot to orders
ALTER TABLE orders ADD COLUMN nombre_domiciliario VARCHAR(200) NULL AFTER id_domiciliario;
UPDATE orders o LEFT JOIN users u ON o.id_domiciliario = u.id
  SET o.nombre_domiciliario = u.nombre WHERE u.id IS NOT NULL;

-- 4. Add nombre_domiciliario snapshot to deliveries
ALTER TABLE deliveries ADD COLUMN nombre_domiciliario VARCHAR(200) NULL AFTER id_domiciliario;
UPDATE deliveries d LEFT JOIN users u ON d.id_domiciliario = u.id
  SET d.nombre_domiciliario = u.nombre WHERE u.id IS NOT NULL;

-- 5. Add precio_compra_unitario_kg snapshot to order_items
ALTER TABLE order_items ADD COLUMN precio_compra_unitario_kg DECIMAL(12,4) NOT NULL DEFAULT 0 AFTER precio_unitario_kg;

-- 6. Add precio_compra_unitario_kg snapshot to delivery_items (if not already exists)
ALTER TABLE delivery_items ADD COLUMN precio_compra_unitario_kg DECIMAL(12,4) NOT NULL DEFAULT 0 AFTER cantidad_kg;

-- 7. Add precio_compra_kg to products (if not already exists)
ALTER TABLE products ADD COLUMN precio_compra_kg DECIMAL(12,4) NOT NULL DEFAULT 0 AFTER precio;

-- 8. Add estado column to deliveries (if not already exists from migration 002)
-- Skip if already done: ALTER TABLE deliveries ADD COLUMN estado ENUM('pendiente','en_proceso','completada','cancelada') NOT NULL DEFAULT 'pendiente';

-- 9. Add id_vehiculo to orders (if not already done)
-- Skip if already done: ALTER TABLE orders ADD COLUMN id_vehiculo INT NULL;

-- Done! Restart the backend after running this script.
