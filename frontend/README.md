# 🚀 Full-Stack Sales Analytics & Automated ETL Platform

An enterprise-grade sales analytics platform and automated ETL pipeline built with **PostgreSQL**, **Python (FastAPI + Pandas)**, and **React.js (Tailwind CSS + Recharts)**.

Users can upload raw CSV datasets, automatically validate and clean data through an ETL pipeline, persist structured records in PostgreSQL with idempotent upserts, quarantine dirty records with exact rejection diagnostics, and view dynamic real-time analytical dashboards.

**GitHub Repository:** [https://github.com/adityaam2904/Sales_analytics_Dashboard](https://github.com/adityaam2904/Sales_analytics_Dashboard)

---

## 🛠️ System Architecture & Technology Stack

| Layer | Technologies | Key Responsibilities |
| :--- | :--- | :--- |
| **Frontend** | React 18 (Vite), Tailwind CSS, Recharts, React Router, Axios | Executive KPI cards, interactive sales charts, CSV upload staging portal, server-side paginated data tables, and live ETL execution console. |
| **Backend REST API** | Python 3.10+, FastAPI, SQLAlchemy, Pydantic, Uvicorn | RESTful endpoints for multipart file uploads, ETL pipeline orchestration, paginated filtering APIs, and analytical SQL aggregations. |
| **ETL Engine** | Pandas, NumPy, hashlib | CSV parsing, schema normalization, regex validation, mathematical recalculations, quarantine separation, and idempotent upserts to PostgreSQL. |
| **Database** | PostgreSQL | 3 core business tables + 4 ETL tracking tables with primary/foreign keys, check constraints, composite unique constraints, JSONB error storage, and B-Tree indexes. |

---

## 📂 Project Structure

```text
Sales_analytics_Dashboard/
│
├── database/
│   └── schema.sql              # 7-table schema with constraints, indexes & JSONB
│
├── sample_data/                # Edge-case test CSV datasets
│   ├── customers.csv           # Includes duplicate IDs & invalid email formats
│   ├── products.csv            # Includes negative prices & stock edge cases
│   ├── orders.csv              # Includes orphan customer references & negative quantities
│   └── customers_batch2.csv    # Incremental dataset with new, updated & unchanged records
│
├── backend/
│   ├── main.py                 # FastAPI application root, CORS & router registrations
│   ├── requirements.txt        # Backend dependencies
│   ├── .env                    # Database credentials
│   ├── uploads/                # Staging directory for uploaded CSVs
│   └── app/
│       ├── database.py         # SQLAlchemy engine, connection pool & session generator
│       ├── etl/
│       │   ├── cleaners.py     # Pandas cleaning, regex & row rejection logic
│       │   ├── loader.py       # Idempotent upsert logic & FK in-memory pre-validation
│       │   └── pipeline.py     # Pipeline orchestrator, entity hierarchy & DB logging
│       └── routers/
│           ├── uploads.py      # Upload endpoint & SHA-256 duplicate checking
│           ├── etl.py          # Trigger ETL, run histories, logs & rejected rows
│           ├── dashboard.py    # Analytical queries (revenue, monthly trend, top items)
│           └── data.py         # Paginated customer, product & order exploration
│
├── frontend/
│   ├── src/
│   │   ├── api/axios.js        # Axios instance configured for FastAPI baseURL
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx   # Sales KPIs & Recharts visualizations
│   │   │   ├── Customers.jsx   # Customer table, search, filters & order history modal
│   │   │   ├── Products.jsx    # Products catalog, inventory status & revenue stats
│   │   │   ├── Orders.jsx      # Order transactions and status filters
│   │   │   ├── Upload.jsx      # CSV upload portal & duplicate hash warning
│   │   │   └── ETLMonitor.jsx  # Pipeline trigger, live logs & rejected rows inspector
│   │   ├── App.jsx             # Sidebar navigation & React Router setup
│   │   └── index.css           # Tailwind CSS directives
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

---

## 💾 Database Architecture (7 Tables)

### Business Domain:
* **`customers`**: Stores verified customer profiles (`customer_id` [PK], `name`, `email` [UNIQUE], `city`, `country`, `signup_date`).
* **`products`**: Product catalog (`product_id` [PK], `name`, `category`, `unit_price` [CHECK > 0], `stock_quantity` [CHECK >= 0]).
* **`orders`**: Sales transactions (`order_id` [PK], `customer_id` [FK], `product_id` [FK], `quantity` [CHECK > 0], `unit_price`, `discount_pct`, `total_amount`, `order_date`, `status`). All financial amounts use `NUMERIC(12, 2)` to eliminate floating-point rounding errors.

### ETL & Monitoring Domain:
* **`uploaded_files`**: Tracks every file uploaded with its **SHA-256 hash** (`CHAR(64)`) to block duplicate uploads before ingestion.
* **`etl_runs`**: Records run metadata (`mode`, `status`, `rows_read`, `rows_inserted`, `rows_updated`, `rows_unchanged`, `rows_rejected`, `duration_seconds`).
* **`etl_logs`**: Line-by-line runtime logs (`INFO`, `WARNING`, `ERROR`) linked to specific runs.
* **`rejected_records`**: Quarantines dirty records with exact failure reasons and original inputs stored in **`JSONB`**, enforced by a composite unique constraint `(upload_id, row_number)`.

---

## ⚡ Complete Setup & Execution Guide

Follow these steps sequentially to set up and run the entire platform from scratch:

### Step 1: Clone the Repository
```bash
git clone https://github.com/adityaam2904/Sales_analytics_Dashboard.git
cd Sales_analytics_Dashboard
```

---

### Step 2: Database Initialization (PostgreSQL)

1. Ensure your local PostgreSQL service is running (via pgAdmin or service manager).
2. Open your terminal or `psql` console to create the database:
   ```bash
   psql -U postgres -c "CREATE DATABASE sales_analytics;"
   ```
3. Run the schema file to create all 7 tables, check constraints, foreign keys, and B-Tree indexes:
   ```bash
   psql -U postgres -d sales_analytics -f database/schema.sql
   ```
4. Verify table creation:
   ```bash
   psql -U postgres -d sales_analytics -c "\dt"
   ```
   *(You should see exactly 7 tables: `customers`, `products`, `orders`, `uploaded_files`, `etl_runs`, `etl_logs`, `rejected_records`)*.

---

### Step 3: Backend Setup & Execution (FastAPI)

1. Open a new terminal and navigate to the `backend/` folder:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # Windows:
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux:
   # python3 -m venv venv
   # source venv/bin/activate
   ```
3. Install the required backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your environment variables in `backend/.env`:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=sales_analytics
   DB_USER=postgres
   DB_PASSWORD=your_postgres_password
   UPLOAD_DIR=uploads
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```
   * **API Service Running:** `http://127.0.0.1:8000`
   * **Interactive Swagger Documentation:** `http://127.0.0.1:8000/docs`

---

### Step 4: Frontend Setup & Execution (React.js)

1. Open a second terminal window and navigate to the `frontend/` folder:
   ```bash
   cd frontend
   ```
2. Install frontend packages:
   ```bash
   npm install
   ```
3. Launch the Vite local development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```

---

## 🧪 End-to-End System Workflow Execution

Once both servers are running, follow this exact sequence to populate and verify your platform:

### 1. Upload Datasets (`/upload`)
1. Click **Upload Data** in the left sidebar (`http://localhost:5173/upload`).
2. Upload the baseline CSV files from the `sample_data/` folder **in order of entity hierarchy**:
   * Select **Entity Type: Customers** $\rightarrow$ choose `sample_data/customers.csv` $\rightarrow$ click **Upload CSV to Staging**.
   * Select **Entity Type: Products** $\rightarrow$ choose `sample_data/products.csv` $\rightarrow$ click **Upload CSV to Staging**.
   * Select **Entity Type: Orders** $\rightarrow$ choose `sample_data/orders.csv` $\rightarrow$ click **Upload CSV to Staging**.
3. **Duplicate Detection Test:** Try uploading `customers.csv` a second time. The system will display an **amber duplicate warning banner**, demonstrating content-based SHA-256 hash deduplication.

### 2. Execute the ETL Pipeline (`/etl`)
1. Click **ETL Monitor** in the left sidebar (`http://localhost:5173/etl`).
2. Select **Incremental Mode** and click **🚀 Trigger Pipeline**.
3. Watch the dark terminal viewer display real-time execution logs (`INFO`, `WARNING`, `ERROR`).
4. Switch to the **"Quarantined Rejected Records"** tab:
   * Observe how dirty records (e.g. invalid emails, negative prices, and orphan foreign key references) were safely intercepted and stored in `rejected_records` with raw JSON payloads without crashing the batch.

### 3. Verify the Analytics Dashboard (`/`)
1. Click **Dashboard** in the sidebar.
2. View real-time aggregated metrics:
   * **4 Executive KPI Cards:** Total Revenue, Total Orders, Active Customers, Average Order Value.
   * **Monthly Revenue Trend:** Interactive Recharts line chart showing month-over-month revenue curves.
   * **Revenue by Category:** Donut/Pie chart displaying percentage distribution across categories.
   * **Top 5 Products:** Horizontal bar chart ranking best-selling catalog items.
   * **Order Status Breakdown:** Grid summary of orders by status.

### 4. Test Incremental Loading (`/upload` & `/etl`)
1. Go back to **Upload Data** and upload `sample_data/customers_batch2.csv`.
2. Return to **ETL Monitor** and click **Trigger Pipeline**.
3. Observe the row metrics in the run history:
   * New customers are inserted.
   * Existing customers with modified details are updated in-place.
   * Unchanged customers are skipped.
   * **Zero duplicate records are created in PostgreSQL**, confirming full pipeline idempotency.

### 5. Explore Data Tables (`/customers`, `/products`, `/orders`)
* **Customers:** Search by customer name/email, filter by country dropdown, paginate across pages, and click **"View Orders"** to drill down into a customer's specific purchase history in a modal.
* **Products:** Filter catalog items by category and observe color-coded low-stock inventory warning badges.
* **Orders:** Inspect transaction records with status tags (`completed`, `shipped`, `pending`, `cancelled`, `returned`).