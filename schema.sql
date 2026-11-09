-- =============================================================================
-- Clipeus Virtutis® - Official PostgreSQL Database Schema
-- Multi-Sector B2B Trade Gateway & Laboratory Administration
-- =============================================================================

-- 1. Admin Users Table
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'superadmin',
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed default Administrator: Lab / lab@2026
-- (SHA-256 for lab@2026 is e0c4f826620573c246f4ebc93f0b0946b216518fb92797746522ef87c800ea65)
INSERT INTO admin_users (username, password_hash, role)
VALUES ('Lab', 'e0c4f826620573c246f4ebc93f0b0946b216518fb92797746522ef87c800ea65', 'superadmin')
ON CONFLICT (username) DO NOTHING;

-- 2. Products Catalog Table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(120) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subtitle VARCHAR(255),
    sku VARCHAR(100),
    moq VARCHAR(100) DEFAULT '1 Metric Ton',
    incoterms VARCHAR(100) DEFAULT 'CIF / FOB (Port of Chennai)',
    accreditation VARCHAR(255) DEFAULT 'NABL ISO/IEC 17025 Accredited',
    description TEXT,
    formulation TEXT,
    image_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Commercial Enquiries & RFQ Dockets Table
CREATE TABLE IF NOT EXISTS enquiries (
    id SERIAL PRIMARY KEY,
    reference_no VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(100),
    volume VARCHAR(100),
    incoterm VARCHAR(50) DEFAULT 'CIF',
    destination_port VARCHAR(255),
    products_requested TEXT,
    sample_kit_requested BOOLEAN DEFAULT FALSE,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'New', -- 'New', 'In Review', 'Quoted', 'Sample Dispatched', 'Closed'
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indices for rapid analytics and filtering
CREATE INDEX IF NOT EXISTS idx_enquiries_created_at ON enquiries(created_at);
CREATE INDEX IF NOT EXISTS idx_enquiries_status ON enquiries(status);
CREATE INDEX IF NOT EXISTS idx_enquiries_ref ON enquiries(reference_no);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);
