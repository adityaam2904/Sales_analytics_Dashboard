# 🚀 Full-Stack Sales Analytics, Automated ETL & AI Platform

An enterprise-grade sales analytics platform and automated ETL pipeline built with **PostgreSQL**, **Python (FastAPI + Pandas)**, **React.js (Tailwind CSS + Recharts)**, and **Google Gemini GenAI**.

Users can upload raw CSV datasets, automatically validate and clean data through an ETL pipeline, persist structured records in PostgreSQL with idempotent upserts, quarantine dirty records with exact rejection diagnostics, view dynamic real-time analytical dashboards, and interact with a live **AI Sales Assistant** connected directly to the database.

**GitHub Repository:** [https://github.com/adityaam2904/Sales_analytics_Dashboard](https://github.com/adityaam2904/Sales_analytics_Dashboard)

---

## 🛠️ System Architecture & Technology Stack

| Layer | Technologies | Key Responsibilities |
| :--- | :--- | :--- |
| **Frontend** | React 18 (Vite), Tailwind CSS, Recharts, React Router, React Markdown, Axios | Executive KPI cards, interactive sales charts, CSV upload staging portal, server-side paginated data tables, live ETL execution console, and AI Chatbot interface. |
| **Backend REST API** | Python 3.10+, FastAPI, SQLAlchemy, Pydantic, Uvicorn | RESTful endpoints for multipart file uploads, ETL pipeline orchestration, paginated filtering APIs, analytical SQL aggregations, and AI prompt engineering with live DB context. |
| **ETL Engine** | Pandas, NumPy, hashlib | CSV parsing, schema normalization, regex validation, mathematical recalculations, quarantine separation, and idempotent upserts to PostgreSQL. |
| **Database** | PostgreSQL | 3 core business tables + 4 ETL tracking tables with primary/foreign keys, check constraints, composite unique constraints, JSONB error storage, and B-Tree indexes. |
| **AI Layer** | Google GenAI SDK (`gemini-3.5-flash-lite`, `gemini-3.8-flash`) | Context-aware AI assistant querying live PostgreSQL metrics to answer natural language business questions. |

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
│   ├── .env                    # Database credentials & Gemini API Key
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
│           ├── data.py         # Paginated customer, product & order exploration
│           └── chat.py         # AI chatbot endpoint with dynamic PostgreSQL context
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
│   │   │   ├── ETLMonitor.jsx  # Pipeline trigger, live logs & rejected rows inspector
│   │   │   └── Chat.jsx        # AI Assistant with live DB context & markdown rendering
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
* **`products`**: Product catalog (`product_id` [PK], `name`, `category`, `unit_price` [CHECK > 0], `stock` [CHECK >= 0]).
* **`orders`**: Sales transactions (`order_id` [PK], `customer_id` [FK], `product_id` [FK], `quantity` [CHECK > 0], `unit_price`, `discount_pct`, `total_amount`, `order_date`, `status`).

### ETL & Monitoring Domain:
* **`uploaded_files`**: Tracks every file uploaded with its **SHA-256 hash** (`CHAR(64)`) to block duplicate uploads before ingestion.
* **`etl_runs`**: Records run metadata (`mode`, `status`, `rows_read`, `rows_inserted`, `rows_updated`, `rows_unchanged`, `rows_rejected`, `duration`).
* **`etl_logs`**: Line-by-line runtime logs (`INFO`, `WARNING`, `ERROR`) linked to specific runs.
* **`rejected_records`**: Quarantines dirty records with exact failure reasons and original inputs stored in **`JSONB`**, enforced by a composite unique constraint `(upload_id, row_number)`.

---

## ⚡ Setup & Execution Guide

### 1. Database Setup
Ensure PostgreSQL is running locally and execute the schema:
```bash
psql -U postgres -c "CREATE DATABASE sales_analytics;"
psql -U postgres -d sales_analytics -f database/schema.sql
```

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables in backend/.env:
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=sales_analytics
# DB_USER=postgres
# DB_PASSWORD=your_password
# UPLOAD_DIR=uploads
# GEMINI_API_KEY=your_gemini_api_key

# Start the FastAPI server
uvicorn main:app --reload
```
* **Interactive Swagger API Documentation:** `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
Open a second terminal:
```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
* **Web Application:** `http://localhost:5173/`

---

## 🧪 Testing the Complete System Workflow

1. **Upload Datasets**:
   - Navigate to **📁 Upload CSV** (`/upload`).
   - Upload `sample_data/customers.csv`, `products.csv`, and `orders.csv`.
   - Re-uploading `customers.csv` immediately displays a duplicate file warning via SHA-256 validation.
2. **Execute ETL**:
   - Navigate to **⚙️ ETL Monitor** (`/etl`).
   - Click **"🚀 Trigger Pipeline"**.
   - Observe real-time logs in the execution terminal.
   - Switch to **"Quarantined Rejected Records"** to verify that malformed rows (e.g. invalid emails, negative prices, orphan customer foreign keys) were quarantined with raw JSON payloads without crashing the batch.
3. **Analytics Dashboard**:
   - Navigate to **📊 Dashboard** (`/`) to view live KPIs, monthly revenue curves, category distribution, and top-selling products.
4. **Incremental Loading Test**:
   - Upload `sample_data/customers_batch2.csv` and trigger ETL.
   - Verify that new records are inserted, modified records updated in-place, and identical records skipped with zero duplicates created.
5. **AI Sales Assistant**:
   - Navigate to **💬 AI Assistant** (`/chat`).
   - Ask natural language questions like *"Who is our top spending customer?"* or *"What is our revenue breakdown by category?"* to see live database numbers synthesized into executive summaries.