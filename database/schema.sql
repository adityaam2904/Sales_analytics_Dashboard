-- 1. CUSTOMERS
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    city VARCHAR(80) NOT NULL DEFAULT 'Unknown',
    country VARCHAR(80) NOT NULL DEFAULT 'Unknown',
    signup_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
select * from customers;
-- 2. PRODUCTS
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(80) NOT NULL DEFAULT 'Uncategorized',
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price > 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
select * from products;

-- 3. ORDERS
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(30) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL REFERENCES customers(customer_id),
    product_id VARCHAR(20) NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    discount_pct NUMERIC(5, 2) NOT NULL DEFAULT 0 CHECK (discount_pct BETWEEN 0 AND 100),
    total_amount NUMERIC(14, 2) NOT NULL CHECK (total_amount >= 0),
    order_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('completed', 'shipped', 'pending', 'cancelled', 'returned')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_product ON orders(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);

-- =====================================================================
-- ETL METADATA & MONITORING TABLES (4 tables)
-- =====================================================================

-- 1. ETL Runs: Summary of each batch execution
CREATE TABLE IF NOT EXISTS etl_runs (
    run_id SERIAL PRIMARY KEY,
    mode VARCHAR(20) NOT NULL DEFAULT 'incremental' 
        CHECK (mode IN ('incremental', 'full_reload')),
    status VARCHAR(20) NOT NULL DEFAULT 'running' 
        CHECK (status IN ('running', 'success', 'partial', 'failed')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    files_processed INTEGER NOT NULL DEFAULT 0,
    rows_read INTEGER NOT NULL DEFAULT 0,
    rows_inserted INTEGER NOT NULL DEFAULT 0,
    rows_updated INTEGER NOT NULL DEFAULT 0,
    rows_unchanged INTEGER NOT NULL DEFAULT 0,
    rows_rejected INTEGER NOT NULL DEFAULT 0
);

select * from etl_runs;

-- 2. Uploaded Files: Tracks files received via the frontend/API
CREATE TABLE IF NOT EXISTS uploaded_files (
    file_id SERIAL PRIMARY KEY,
    entity VARCHAR(20) NOT NULL 
        CHECK (entity IN ('customers', 'products', 'orders')),
    original_name VARCHAR(255) NOT NULL,
    stored_path TEXT NOT NULL,
    file_hash CHAR(64) NOT NULL, -- SHA-256 hash to detect duplicate file uploads
    size_bytes INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'uploaded' 
        CHECK (status IN ('uploaded', 'processed', 'skipped', 'failed')),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ,
    last_run_id INTEGER REFERENCES etl_runs(run_id) ON DELETE SET NULL,
    rows_read INTEGER NOT NULL DEFAULT 0,
    rows_inserted INTEGER NOT NULL DEFAULT 0,
    rows_updated INTEGER NOT NULL DEFAULT 0,
    rows_unchanged INTEGER NOT NULL DEFAULT 0,
    rows_rejected INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_uploaded_files_hash ON uploaded_files(entity, file_hash);

-- 3. ETL Logs: Real-time logs for each ETL run (visible in dashboard)
CREATE TABLE IF NOT EXISTS etl_logs (
    log_id BIGSERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES etl_runs(run_id) ON DELETE CASCADE,
    level VARCHAR(10) NOT NULL CHECK (level IN ('INFO', 'WARNING', 'ERROR')),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_etl_logs_run ON etl_logs(run_id);

-- 4. Rejected Records: Keeps bad/dirty data quarantined with exact failure reasons
CREATE TABLE IF NOT EXISTS rejected_records (
    reject_id BIGSERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES etl_runs(run_id) ON DELETE CASCADE,
    upload_id INTEGER REFERENCES uploaded_files(file_id) ON DELETE CASCADE,
    entity VARCHAR(20) NOT NULL,
    row_number INTEGER NOT NULL,
    reason TEXT NOT NULL,
    raw_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (upload_id, row_number)
);

CREATE INDEX IF NOT EXISTS idx_rejected_run ON rejected_records(run_id);

