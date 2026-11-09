#!/usr/bin/env python3
"""
Clipeus Virtutis® - Database Layer with Native PostgreSQL & SQLite Adaptive Engine
Supports PostgreSQL (via psycopg2 / pg8000) with automatic zero-config SQLite fallback.
"""

import os
import sys
import hashlib
import json
import uuid
from datetime import datetime, timedelta

# Ensure local workspace lib directory is available for psycopg2 / pg8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(BASE_DIR, 'lib')
if os.path.exists(LIB_DIR) and LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL') or os.environ.get('PG_CONNECTION_STRING')
DB_ENGINE = "sqlite"
pg_conn = None

def hash_password(password: str) -> str:
    """Hash password with SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class DatabaseManager:
    def __init__(self):
        self.engine = "sqlite"
        self.db_path = os.path.join(BASE_DIR, "clipeus.db")
        self.sessions = {} # In-memory active session tokens -> { token: { username, expires } }
        self._init_connection()
        self._create_schema()
        self._seed_initial_data()

    def _init_connection(self):
        """Attempt to connect to PostgreSQL if URL/host is configured, else fallback to SQLite."""
        global DATABASE_URL
        if DATABASE_URL:
            try:
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL)
                conn.close()
                self.engine = "postgresql"
                print(f"✅ [Database] Successfully connected to PostgreSQL via psycopg2")
                return
            except Exception as e:
                try:
                    import pg8000.native
                    # Try pg8000 as pure python driver
                    self.engine = "postgresql_pg8000"
                    print(f"✅ [Database] Using PostgreSQL via pg8000")
                    return
                except Exception as e2:
                    print(f"⚠️ [Database] PostgreSQL connection failed ({e}). Falling back to local SQLite engine.")

        self.engine = "sqlite"
        print(f"ℹ️ [Database] Running with SQLite local storage ({self.db_path}). Set DATABASE_URL to connect to PostgreSQL.")

    def get_connection(self):
        """Get an active database connection."""
        if self.engine == "postgresql":
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(DATABASE_URL)
            conn.autocommit = True
            return conn
        else:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

    def _create_schema(self):
        """Create tables if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        if self.engine == "postgresql":
            # PostgreSQL Schema
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'superadmin',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                slug VARCHAR(120) UNIQUE NOT NULL,
                title VARCHAR(255) NOT NULL,
                category VARCHAR(100) NOT NULL,
                subtitle VARCHAR(255),
                sku VARCHAR(100),
                moq VARCHAR(100) DEFAULT '1 Metric Ton',
                incoterms VARCHAR(100) DEFAULT 'CIF / FOB',
                accreditation VARCHAR(255) DEFAULT 'NABL ISO/IEC 17025 Accredited',
                description TEXT,
                formulation TEXT,
                image_url TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
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
                status VARCHAR(50) DEFAULT 'New',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """)
        else:
            # SQLite Schema
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'superadmin',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                subtitle TEXT,
                sku TEXT,
                moq TEXT DEFAULT '1 Metric Ton',
                incoterms TEXT DEFAULT 'CIF / FOB',
                accreditation TEXT DEFAULT 'NABL ISO/IEC 17025 Accredited',
                description TEXT,
                formulation TEXT,
                image_url TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS enquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_no TEXT UNIQUE NOT NULL,
                company_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                volume TEXT,
                incoterm TEXT DEFAULT 'CIF',
                destination_port TEXT,
                products_requested TEXT,
                sample_kit_requested INTEGER DEFAULT 0,
                notes TEXT,
                status TEXT DEFAULT 'New',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)
            conn.commit()

        cursor.close()
        conn.close()

    def _seed_initial_data(self):
        """Seed default admin credentials and standard initial products."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Seed Admin: Lab / lab@2026
        target_username = "Lab"
        target_hash = hash_password("lab@2026")

        if self.engine == "postgresql":
            cursor.execute("SELECT id FROM admin_users WHERE username = %s", (target_username,))
            row = cursor.fetchone()
            if not row:
                cursor.execute(
                    "INSERT INTO admin_users (username, password_hash, role) VALUES (%s, %s, %s)",
                    (target_username, target_hash, 'superadmin')
                )
            else:
                # Update password hash if needed
                cursor.execute(
                    "UPDATE admin_users SET password_hash = %s WHERE username = %s",
                    (target_hash, target_username)
                )
        else:
            cursor.execute("SELECT id FROM admin_users WHERE username = ?", (target_username,))
            row = cursor.fetchone()
            if not row:
                cursor.execute(
                    "INSERT INTO admin_users (username, password_hash, role) VALUES (?, ?, ?)",
                    (target_username, target_hash, 'superadmin')
                )
                conn.commit()
            else:
                cursor.execute(
                    "UPDATE admin_users SET password_hash = ? WHERE username = ?",
                    (target_hash, target_username)
                )
                conn.commit()

        # Seed initial portfolio products if table empty
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        if count == 0:
            initial_products = [
                {
                    "slug": "biglyso-biocompost",
                    "title": "BiGlySo Accelerated Biocompost",
                    "category": "Agro & Soil Science",
                    "subtitle": "NABL ISO 17025 Certified · FCO 1985 Compliant",
                    "sku": "CV-AGRO-BIO-01",
                    "moq": "5 Metric Tons / 1x 20ft FCL",
                    "incoterms": "CIF / FOB (Chennai)",
                    "accreditation": "NABL ISO/IEC 17025 Accredited",
                    "description": "High-potency organic biological compost formulated from microbially pre-digested agro-residues. Enhances soil cation exchange capacity and microbial diversity.",
                    "formulation": "Organic Carbon > 16.5%, C:N Ratio < 18:1, Total NPK > 3.2%",
                    "image_url": "assets/products/biglyso.png"
                },
                {
                    "slug": "eco-bio-bricks",
                    "title": "Compressed Eco Bio-Bricks",
                    "category": "Sustainable Construction",
                    "subtitle": "ASTM C62 Compliant · Carbon-Negative",
                    "sku": "CV-MAT-BRK-04",
                    "moq": "10,000 Units / 1x 40ft FCL",
                    "incoterms": "CIF / FOB (Chennai)",
                    "accreditation": "ASTM / BIS Certified",
                    "description": "Engineered architectural masonry units bound with proprietary mineralized pozzolanic binder. Requires zero high-heat kiln firing, sequestering 0.38kg CO2 per block.",
                    "formulation": "Compressive Strength > 8.5 MPa, Water Absorption < 12%",
                    "image_url": "assets/products/biobrick.png"
                },
                {
                    "slug": "poomannam-incense",
                    "title": "Poomannam Temple Flower Incense",
                    "category": "Sustainable Bio-Products",
                    "subtitle": "Zero Charcoal · IFRA Certified Essential Oils",
                    "sku": "CV-BIO-INC-07",
                    "moq": "1,000 Master Cartons",
                    "incoterms": "CIF / FOB (Chennai)",
                    "accreditation": "ISO 9001:2015",
                    "description": "Artisanal hand-rolled botanical incense produced by upcycling sanctified temple floral waste. 100% charcoal-free, dipped in pure therapeutic oils.",
                    "formulation": "Floral Cellulose Core, Natural Gums, Distilled Botanical Oils",
                    "image_url": "assets/products/incense.png"
                },
                {
                    "slug": "cellulose-extract",
                    "title": "Industrial Cellulose Extract",
                    "category": "Industrial Materials",
                    "subtitle": "High Alpha-Cellulose > 92% · Clean Fiber",
                    "sku": "CV-IND-CEL-09",
                    "moq": "2 Metric Tons",
                    "incoterms": "CIF / FOB (Chennai)",
                    "accreditation": "NABL ISO/IEC 17025 Accredited",
                    "description": "Pure microcrystalline and unbleached technical cellulose fibers derived from reclaimed fibrous crop residues. Ideal for paper, biopolymers, and binder matrices.",
                    "formulation": "Alpha-Cellulose > 92.4%, Moisture < 6%, Ash < 0.8%",
                    "image_url": "assets/products/cellulose.png"
                },
                {
                    "slug": "bio-shoe-polish",
                    "title": "Natural Bio Shoe Polish",
                    "category": "Sustainable Bio-Products",
                    "subtitle": "Zero Petroleum Wax · Pure Carnauba & Beeswax",
                    "sku": "CV-BIO-POL-12",
                    "moq": "2,500 Tins",
                    "incoterms": "CIF / FOB (Chennai)",
                    "accreditation": "REACH Compliant",
                    "description": "Premium biodegradable leather conditioning wax made from refined botanical oils, beeswax, and natural pigments. Non-toxic, deep luster finish.",
                    "formulation": "Beeswax, Carnauba Wax, Cold-Pressed Vegetable Oils, Natural Pigment",
                    "image_url": "assets/products/polish.png"
                },
                {
                    "slug": "pilot-cleantech-plant",
                    "title": "Turnkey Cleantech Pilot System (TRL-7)",
                    "category": "Clean Technology",
                    "subtitle": "TRL-7 Validated · Modular Agro-Waste Valorization",
                    "sku": "CV-ENG-TRL7-01",
                    "moq": "1 Complete Modular Skid",
                    "incoterms": "DDP / CIF Worldwide",
                    "accreditation": "TRL-7 Validated · NABL Certified",
                    "description": "Continuous multi-stage thermal and enzymatic pilot conversion reactor skid. Processes 2.5 MT/day agricultural biomass into certified biocompost and cellulose slurry.",
                    "formulation": "SS316 Fluid Contact, Automated PLC Control, Zero Effluent",
                    "image_url": "assets/products/pilot_plant.png"
                }
            ]

            for p in initial_products:
                if self.engine == "postgresql":
                    cursor.execute("""
                    INSERT INTO products (slug, title, category, subtitle, sku, moq, incoterms, accreditation, description, formulation, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (slug) DO NOTHING;
                    """, (
                        p["slug"], p["title"], p["category"], p["subtitle"], p["sku"],
                        p["moq"], p["incoterms"], p["accreditation"], p["description"],
                        p["formulation"], p["image_url"]
                    ))
                else:
                    cursor.execute("""
                    INSERT OR IGNORE INTO products (slug, title, category, subtitle, sku, moq, incoterms, accreditation, description, formulation, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        p["slug"], p["title"], p["category"], p["subtitle"], p["sku"],
                        p["moq"], p["incoterms"], p["accreditation"], p["description"],
                        p["formulation"], p["image_url"]
                    ))
            if self.engine != "postgresql":
                conn.commit()

        # Seed sample historical enquiries if table is empty (so the last 6 months dashboard has rich analytics)
        cursor.execute("SELECT COUNT(*) FROM enquiries")
        e_count = cursor.fetchone()[0]
        if e_count == 0:
            now = datetime.now()
            # Distribute 18 realistic commercial enquiries across today, this week, this month, and past 6 months
            seed_samples = [
                # Today
                {"ref": "CV-RFQ-2026-9042", "co": "Nordic BioVenture AB", "email": "procure@nordicbio.se", "phone": "+46 8 123 4567", "vol": "25 MT", "inc": "CIF", "port": "Rotterdam", "prod": "BiGlySo Accelerated Biocompost", "sample": 1, "status": "New", "days_ago": 0},
                {"ref": "CV-RFQ-2026-9039", "co": "AgriCore Deutschland GmbH", "email": "trade@agricore.de", "phone": "+49 40 556677", "vol": "1x 40ft FCL", "inc": "CIF", "port": "Hamburg", "prod": "Compressed Eco Bio-Bricks", "sample": 0, "status": "In Review", "days_ago": 0},
                # This Week
                {"ref": "CV-RFQ-2026-8980", "co": "Dubai Green Infrastructure Ltd", "email": "projects@dubaigreen.ae", "phone": "+971 4 889 0012", "vol": "50,000 Units", "inc": "CIF", "port": "Jebel Ali", "prod": "Compressed Eco Bio-Bricks", "sample": 1, "status": "Quoted", "days_ago": 2},
                {"ref": "CV-RFQ-2026-8945", "co": "SingaMaterials PTE", "email": "purchasing@singamaterials.sg", "phone": "+65 6789 0123", "vol": "10 MT", "inc": "FOB", "port": "Singapore", "prod": "Industrial Cellulose Extract", "sample": 1, "status": "New", "days_ago": 4},
                # This Month
                {"ref": "CV-RFQ-2026-8812", "co": "Hellenic Agro Corporation", "email": "imports@hellenicagro.gr", "phone": "+30 210 998877", "vol": "40 MT", "inc": "CIF", "port": "Piraeus", "prod": "BiGlySo Accelerated Biocompost", "sample": 0, "status": "Sample Dispatched", "days_ago": 10},
                {"ref": "CV-RFQ-2026-8790", "co": "EcoBuild UK Limited", "email": "commercial@ecobuilduk.co.uk", "phone": "+44 20 7946 0991", "vol": "20,000 Units", "inc": "CIF", "port": "Felixstowe", "prod": "Compressed Eco Bio-Bricks", "sample": 1, "status": "Quoted", "days_ago": 18},
                # 1 Month Ago (October)
                {"ref": "CV-RFQ-2026-8650", "co": "Tokyo BioPolymers Corp", "email": "source@tokyobiopolymers.jp", "phone": "+81 3 5555 0144", "vol": "8 MT", "inc": "CIF", "port": "Yokohama", "prod": "Industrial Cellulose Extract", "sample": 1, "status": "Closed", "days_ago": 35},
                {"ref": "CV-RFQ-2026-8610", "co": "Gulf Fertilizers WLL", "email": "procurement@gulffert.qa", "phone": "+974 4455 6677", "vol": "60 MT", "inc": "CIF", "port": "Hamad Port", "prod": "BiGlySo Accelerated Biocompost", "sample": 0, "status": "Closed", "days_ago": 42},
                {"ref": "CV-RFQ-2026-8575", "co": "Aura Wellness LLC", "email": "supply@aurawellness.com", "phone": "+1 212 555 0199", "vol": "5,000 Cartons", "inc": "CIF", "port": "New York", "prod": "Poomannam Temple Flower Incense", "sample": 1, "status": "Closed", "days_ago": 50},
                # 2 Months Ago (September)
                {"ref": "CV-RFQ-2026-8430", "co": "Bavaria BioChemicals AG", "email": "trade@bavariabio.de", "phone": "+49 89 234567", "vol": "15 MT", "inc": "CIF", "port": "Rotterdam", "prod": "Industrial Cellulose Extract", "sample": 0, "status": "Closed", "days_ago": 68},
                {"ref": "CV-RFQ-2026-8390", "co": "Emirates Sustainable Living", "email": "ops@emiratesgreen.ae", "phone": "+971 2 445 8899", "vol": "35,000 Units", "inc": "CIF", "port": "Jebel Ali", "prod": "Compressed Eco Bio-Bricks", "sample": 1, "status": "Closed", "days_ago": 75},
                # 3 Months Ago (August)
                {"ref": "CV-RFQ-2026-8210", "co": "GreenVenture Australia Pty", "email": "docket@greenventure.com.au", "phone": "+61 2 9876 5432", "vol": "100 MT", "inc": "CIF", "port": "Melbourne", "prod": "BiGlySo Accelerated Biocompost", "sample": 1, "status": "Closed", "days_ago": 98},
                {"ref": "CV-RFQ-2026-8150", "co": "Milan EcoLeather S.r.l.", "email": "acquisti@milanecoleather.it", "phone": "+39 02 887766", "vol": "10,000 Tins", "inc": "CIF", "port": "Genoa", "prod": "Natural Bio Shoe Polish", "sample": 1, "status": "Closed", "days_ago": 110},
                # 4 Months Ago (July)
                {"ref": "CV-RFQ-2026-7950", "co": "Durban Agricultural Syndicate", "email": "imports@durbanagro.co.za", "phone": "+27 31 300 4000", "vol": "50 MT", "inc": "CIF", "port": "Durban", "prod": "BiGlySo Accelerated Biocompost", "sample": 0, "status": "Closed", "days_ago": 130},
                {"ref": "CV-RFQ-2026-7880", "co": "ASEAN CleanTech Consortium", "email": "pilot@aseancleantech.org", "phone": "+60 3 2145 6789", "vol": "1 Pilot Unit", "inc": "DDP", "port": "Port Klang", "prod": "Turnkey Cleantech Pilot System (TRL-7)", "sample": 1, "status": "Closed", "days_ago": 145},
                # 5 Months Ago (June)
                {"ref": "CV-RFQ-2026-7720", "co": "Iberia BioSolutions SL", "email": "compras@iberiabio.es", "phone": "+34 91 556 7890", "vol": "30 MT", "inc": "CIF", "port": "Valencia", "prod": "BiGlySo Accelerated Biocompost", "sample": 0, "status": "Closed", "days_ago": 160},
                {"ref": "CV-RFQ-2026-7640", "co": "Seoul Circular Materials", "email": "trade@seoulcircular.kr", "phone": "+82 2 3456 7890", "vol": "12 MT", "inc": "CIF", "port": "Busan", "prod": "Industrial Cellulose Extract", "sample": 1, "status": "Closed", "days_ago": 175}
            ]

            for s in seed_samples:
                date_str = (now - timedelta(days=s["days_ago"])).strftime("%Y-%m-%d %H:%M:%S")
                if self.engine == "postgresql":
                    cursor.execute("""
                    INSERT INTO enquiries (reference_no, company_name, email, phone, volume, incoterm, destination_port, products_requested, sample_kit_requested, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (reference_no) DO NOTHING;
                    """, (
                        s["ref"], s["co"], s["email"], s["phone"], s["vol"], s["inc"], s["port"],
                        s["prod"], bool(s["sample"]), s["status"], date_str
                    ))
                else:
                    cursor.execute("""
                    INSERT OR IGNORE INTO enquiries (reference_no, company_name, email, phone, volume, incoterm, destination_port, products_requested, sample_kit_requested, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        s["ref"], s["co"], s["email"], s["phone"], s["vol"], s["inc"], s["port"],
                        s["prod"], s["sample"], s["status"], date_str
                    ))
            if self.engine != "postgresql":
                conn.commit()

        cursor.close()
        conn.close()

    # -------------------------------------------------------------------------
    # Authentication & Session Management
    # -------------------------------------------------------------------------
    def authenticate(self, username, password):
        """Validate credentials for admin login: Username: Lab, Password: lab@2026."""
        if not username or not password:
            return None
        
        # Immediate direct verification matching user exact specifications
        if username.strip() == "Lab" and password.strip() == "lab@2026":
            token = str(uuid.uuid4())
            self.sessions[token] = {
                "username": "Lab",
                "role": "superadmin",
                "expires": datetime.now() + timedelta(days=7)
            }
            return {
                "token": token,
                "username": "Lab",
                "role": "superadmin"
            }

        # Also fallback check against database
        conn = self.get_connection()
        cursor = conn.cursor()
        p_hash = hash_password(password.strip())

        user = None
        if self.engine == "postgresql":
            cursor.execute("SELECT id, username, role FROM admin_users WHERE username = %s AND password_hash = %s", (username.strip(), p_hash))
            row = cursor.fetchone()
            if row:
                user = {"id": row[0], "username": row[1], "role": row[2]}
        else:
            cursor.execute("SELECT id, username, role FROM admin_users WHERE username = ? AND password_hash = ?", (username.strip(), p_hash))
            row = cursor.fetchone()
            if row:
                user = {"id": row["id"], "username": row["username"], "role": row["role"]}

        cursor.close()
        conn.close()

        if user:
            token = str(uuid.uuid4())
            self.sessions[token] = {
                "username": user["username"],
                "role": user["role"],
                "expires": datetime.now() + timedelta(days=7)
            }
            return {
                "token": token,
                "username": user["username"],
                "role": user["role"]
            }
        return None

    def verify_token(self, token):
        """Check if session token is valid."""
        if not token or token not in self.sessions:
            return None
        session = self.sessions[token]
        if datetime.now() > session["expires"]:
            del self.sessions[token]
            return None
        return session

    def logout(self, token):
        """Invalidate session."""
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False

    # -------------------------------------------------------------------------
    # Enquiries & Analytics
    # -------------------------------------------------------------------------
    def create_enquiry(self, data):
        """Store an enquiry from front-end RFQ docket or contact page."""
        ref_no = f"CV-RFQ-2026-{datetime.now().strftime('%M%S')}{uuid.uuid4().hex[:2].upper()}"
        company = data.get("company_name") or data.get("company") or "Trade Partner"
        email = data.get("email") or ""
        phone = data.get("phone") or ""
        volume = data.get("volume") or "Commercial Trial"
        incoterm = data.get("incoterm") or "CIF"
        port = data.get("destination_port") or data.get("port") or "Global Port"
        products = data.get("products_requested") or data.get("docket_products") or "Trade Inquiry"
        sample_kit = 1 if data.get("sample_kit_requested") or data.get("sample") else 0
        notes = data.get("notes") or ""
        status = "New"

        conn = self.get_connection()
        cursor = conn.cursor()

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.engine == "postgresql":
            cursor.execute("""
            INSERT INTO enquiries (reference_no, company_name, email, phone, volume, incoterm, destination_port, products_requested, sample_kit_requested, notes, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """, (
                ref_no, company, email, phone, volume, incoterm, port, products, bool(sample_kit), notes, status, created_at
            ))
            new_id = cursor.fetchone()[0]
        else:
            cursor.execute("""
            INSERT INTO enquiries (reference_no, company_name, email, phone, volume, incoterm, destination_port, products_requested, sample_kit_requested, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                ref_no, company, email, phone, volume, incoterm, port, products, sample_kit, notes, status, created_at
            ))
            new_id = cursor.lastrowid
            conn.commit()

        cursor.close()
        conn.close()

        return {
            "id": new_id,
            "reference_no": ref_no,
            "company_name": company,
            "email": email,
            "phone": phone,
            "volume": volume,
            "incoterm": incoterm,
            "destination_port": port,
            "products_requested": products,
            "sample_kit_requested": bool(sample_kit),
            "status": status,
            "created_at": created_at
        }

    def update_enquiry_status(self, ref_or_id, new_status):
        """Update enquiry status (New, In Review, Quoted, Sample Dispatched, Closed)."""
        conn = self.get_connection()
        cursor = conn.cursor()

        if self.engine == "postgresql":
            cursor.execute("UPDATE enquiries SET status = %s WHERE reference_no = %s OR CAST(id AS TEXT) = %s", (new_status, str(ref_or_id), str(ref_or_id)))
        else:
            cursor.execute("UPDATE enquiries SET status = ? WHERE reference_no = ? OR CAST(id AS TEXT) = ?", (new_status, str(ref_or_id), str(ref_or_id)))
            conn.commit()

        cursor.close()
        conn.close()
        return True

    def get_dashboard_metrics(self):
        """
        Calculate total enquiry statistics for:
        - Day (Today)
        - Week (This Week - last 7 days)
        - Month (This Month - calendar month)
        - Yearly (This Year - 2026)
        - Last 6 Months (Month-by-month volume breakdown)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now()
        today_start = now.strftime("%Y-%m-%d 00:00:00")
        week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
        month_start = now.strftime("%Y-%m-01 00:00:00")
        year_start = now.strftime("%Y-01-01 00:00:00")

        # Queries
        if self.engine == "postgresql":
            cursor.execute("SELECT COUNT(*) FROM enquiries WHERE created_at >= %s", (today_start,))
            day_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM enquiries WHERE created_at >= %s", (week_start,))
            week_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM enquiries WHERE created_at >= %s", (month_start,))
            month_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM enquiries WHERE created_at >= %s", (year_start,))
            year_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM enquiries")
            total_all_time = cursor.fetchone()[0]

            # Fetch all enquiries to build last 6 months breakdown
            cursor.execute("SELECT created_at, status FROM enquiries ORDER BY created_at DESC")
            all_rows = cursor.fetchall()
        else:
            cursor.execute("SELECT COUNT(*) FROM enquiries WHERE created_at >= ?", (today_start,))
            day_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM enquiries WHERE created_at >= ?", (week_start,))
            week_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM enquiries WHERE created_at >= ?", (month_start,))
            month_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM enquiries WHERE created_at >= ?", (year_start,))
            year_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM enquiries")
            total_all_time = cursor.fetchone()[0]

            cursor.execute("SELECT created_at, status FROM enquiries ORDER BY created_at DESC")
            all_rows = cursor.fetchall()

        cursor.close()
        conn.close()

        # Build clean Last 6 Months breakdown
        # e.g., November, October, September, August, July, June
        months_breakdown = []
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        for i in range(5, -1, -1):
            # calculate target month and year
            year = now.year
            month = now.month - i
            while month <= 0:
                month += 12
                year -= 1
            
            m_key = f"{year}-{month:02d}"
            m_label = f"{month_names[month-1]} {year}"

            # count enquiries matching this YYYY-MM
            count_m = 0
            for r in all_rows:
                c_at = str(r[0])
                if c_at.startswith(m_key):
                    count_m += 1

            months_breakdown.append({
                "key": m_key,
                "label": m_label,
                "count": count_m
            })

        return {
            "stats": {
                "day": day_count,
                "week": week_count,
                "month": month_count,
                "yearly": year_count,
                "total": total_all_time
            },
            "last_six_months": months_breakdown,
            "database_engine": self.engine
        }

    def get_enquiries(self, limit=100, period="all", search=""):
        """Fetch list of enquiries with filtering."""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT id, reference_no, company_name, email, phone, volume, incoterm, destination_port, products_requested, sample_kit_requested, notes, status, created_at FROM enquiries"
        params = []
        conditions = []

        now = datetime.now()
        if period == "day":
            conditions.append("created_at >= " + ("%s" if self.engine == "postgresql" else "?"))
            params.append(now.strftime("%Y-%m-%d 00:00:00"))
        elif period == "week":
            conditions.append("created_at >= " + ("%s" if self.engine == "postgresql" else "?"))
            params.append((now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00"))
        elif period == "month":
            conditions.append("created_at >= " + ("%s" if self.engine == "postgresql" else "?"))
            params.append(now.strftime("%Y-%m-01 00:00:00"))
        elif period == "six_months":
            conditions.append("created_at >= " + ("%s" if self.engine == "postgresql" else "?"))
            params.append((now - timedelta(days=180)).strftime("%Y-%m-%d 00:00:00"))
        elif period == "yearly":
            conditions.append("created_at >= " + ("%s" if self.engine == "postgresql" else "?"))
            params.append(now.strftime("%Y-01-01 00:00:00"))

        if search:
            placeholder = "%s" if self.engine == "postgresql" else "?"
            search_clause = f"(company_name LIKE {placeholder} OR reference_no LIKE {placeholder} OR email LIKE {placeholder} OR destination_port LIKE {placeholder} OR products_requested LIKE {placeholder})"
            conditions.append(search_clause)
            s_term = f"%{search}%"
            params.extend([s_term, s_term, s_term, s_term, s_term])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {int(limit)}"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        enquiries = []
        for r in rows:
            if self.engine == "postgresql":
                enquiries.append({
                    "id": r[0],
                    "reference_no": r[1],
                    "company_name": r[2],
                    "email": r[3],
                    "phone": r[4],
                    "volume": r[5],
                    "incoterm": r[6],
                    "destination_port": r[7],
                    "products_requested": r[8],
                    "sample_kit_requested": bool(r[9]),
                    "notes": r[10],
                    "status": r[11],
                    "created_at": str(r[12])
                })
            else:
                enquiries.append({
                    "id": r["id"],
                    "reference_no": r["reference_no"],
                    "company_name": r["company_name"],
                    "email": r["email"],
                    "phone": r["phone"],
                    "volume": r["volume"],
                    "incoterm": r["incoterm"],
                    "destination_port": r["destination_port"],
                    "products_requested": r["products_requested"],
                    "sample_kit_requested": bool(r["sample_kit_requested"]),
                    "notes": r["notes"],
                    "status": r["status"],
                    "created_at": str(r["created_at"])
                })

        cursor.close()
        conn.close()
        return enquiries

    # -------------------------------------------------------------------------
    # Products Management
    # -------------------------------------------------------------------------
    def get_products(self, active_only=False):
        """Fetch products catalog."""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT id, slug, title, category, subtitle, sku, moq, incoterms, accreditation, description, formulation, image_url, is_active, created_at FROM products"
        if active_only:
            query += " WHERE is_active = 1" if self.engine != "postgresql" else " WHERE is_active = TRUE"
        query += " ORDER BY id ASC"

        cursor.execute(query)
        rows = cursor.fetchall()

        products = []
        for r in rows:
            if self.engine == "postgresql":
                products.append({
                    "id": r[0], "slug": r[1], "title": r[2], "category": r[3],
                    "subtitle": r[4], "sku": r[5], "moq": r[6], "incoterms": r[7],
                    "accreditation": r[8], "description": r[9], "formulation": r[10],
                    "image_url": r[11], "is_active": bool(r[12]), "created_at": str(r[13])
                })
            else:
                products.append({
                    "id": r["id"], "slug": r["slug"], "title": r["title"], "category": r["category"],
                    "subtitle": r["subtitle"], "sku": r["sku"], "moq": r["moq"], "incoterms": r["incoterms"],
                    "accreditation": r["accreditation"], "description": r["description"], "formulation": r["formulation"],
                    "image_url": r["image_url"], "is_active": bool(r["is_active"]), "created_at": str(r["created_at"])
                })

        cursor.close()
        conn.close()
        return products

    def create_product(self, data):
        """Insert a newly uploaded product from Admin panel."""
        title = data.get("title", "").strip()
        category = data.get("category", "Sustainable Commodities").strip()
        subtitle = data.get("subtitle", "NABL Accredited").strip()
        sku = data.get("sku", f"CV-PROD-{uuid.uuid4().hex[:4].upper()}").strip()
        moq = data.get("moq", "1 Metric Ton").strip()
        incoterms = data.get("incoterms", "CIF / FOB (Chennai)").strip()
        accreditation = data.get("accreditation", "NABL ISO/IEC 17025 Accredited").strip()
        description = data.get("description", "").strip()
        formulation = data.get("formulation", "").strip()
        image_url = data.get("image_url", "logo.png").strip()

        # Generate slug
        slug = "".join(c.lower() if c.isalnum() else "-" for c in title).strip("-")
        if not slug:
            slug = f"product-{uuid.uuid4().hex[:6]}"
        slug = f"{slug}-{uuid.uuid4().hex[:4]}"

        conn = self.get_connection()
        cursor = conn.cursor()

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.engine == "postgresql":
            cursor.execute("""
            INSERT INTO products (slug, title, category, subtitle, sku, moq, incoterms, accreditation, description, formulation, image_url, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
            RETURNING id;
            """, (
                slug, title, category, subtitle, sku, moq, incoterms, accreditation, description, formulation, image_url, created_at
            ))
            new_id = cursor.fetchone()[0]
        else:
            cursor.execute("""
            INSERT INTO products (slug, title, category, subtitle, sku, moq, incoterms, accreditation, description, formulation, image_url, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?);
            """, (
                slug, title, category, subtitle, sku, moq, incoterms, accreditation, description, formulation, image_url, created_at
            ))
            new_id = cursor.lastrowid
            conn.commit()

        cursor.close()
        conn.close()

        return {
            "id": new_id,
            "slug": slug,
            "title": title,
            "category": category,
            "subtitle": subtitle,
            "sku": sku,
            "moq": moq,
            "incoterms": incoterms,
            "accreditation": accreditation,
            "description": description,
            "formulation": formulation,
            "image_url": image_url,
            "is_active": True,
            "created_at": created_at
        }

    def delete_product(self, product_id):
        """Remove a product by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()

        if self.engine == "postgresql":
            cursor.execute("DELETE FROM products WHERE id = %s", (int(product_id),))
        else:
            cursor.execute("DELETE FROM products WHERE id = ?", (int(product_id),))
            conn.commit()

        cursor.close()
        conn.close()
        return True

# Global database instance singleton
db = DatabaseManager()
