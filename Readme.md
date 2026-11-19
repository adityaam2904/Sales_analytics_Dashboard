 #Full-Stack Sales Analytics & ETL Platform

A full-stack data analytics and automated ETL platform built with PostgreSQL, Python (FastAPI + Pandas), and React.js (Tailwind CSS + Recharts).

Users can upload raw CSV datasets, validate and clean data via a Python ETL pipeline, store structured data in PostgreSQL with idempotency (upsert deduplication), quarantine dirty records, and view real-time analytical dashboards.

---

## 🛠️ Architecture & Tech Stack

| Layer | Technologies | Key Responsibilities |
| :--- | :--- | :--- |
| **Frontend** | React 18 (Vite), Tailwind CSS, Recharts, Axios | KPI overview, interactive analytics charts, CSV upload portal, data exploration tables, live ETL logs & execution monitor. |
| **Backend API** | Python 3.10+, FastAPI, SQLAlchemy, Pydantic, Uvicorn | REST APIs for file uploads, pipeline triggering, paginated data tables, aggregation analytics queries, and log streaming. |
| **ETL Engine** | Pandas, NumPy, hashlib | CSV reading, schema validation, regex email check, edge case quarantine, and idempotent upserts to PostgreSQL. |
| **Database** | PostgreSQL | 3 core business tables + 4 ETL tracking tables with foreign keys, check constraints, and indexed analytical queries. |

---

## 📂 Project Structure

```text
sales-analytics-platform/
│
├── database/
│   └── schema.sql              # 7-table schema with constraints and indexes
│
├── sample_data/                # Edge-case test CSV datasets
│   ├── customers.csv           # Includes duplicate IDs and invalid emails
│   ├── products.csv            # Includes negative prices and invalid stock
│   └── orders.csv              # Includes orphan customer references & negative quantities
│
├── backend/
│   ├── main.py                 # FastAPI application root & CORS
│   ├── requirements.txt        # Backend dependencies
│   ├── .env                    # Database credentials
│   ├── uploads/                # File staging storage
│   └── app/
│       ├── database.py         # SQLAlchemy engine & session factory
│       ├── etl/
│       │   ├── cleaners.py     # Pandas cleaning, regex & row rejection logic
│       │   ├── loader.py       # PostgreSQL upsert logic (ON CONFLICT)
│       │   └── pipeline.py     # Pipeline orchestrator & logger
│       └── routers/
│           ├── uploads.py      # Upload endpoint & SHA-256 duplicate checking
│           ├── etl.py          # Trigger ETL, run histories, logs & rejected rows
│           ├── dashboard.py    # Analytical queries (revenue, monthly trend, top items)
│           └── data.py         # Paginated customer, product & order exploration
│
├── frontend/
│   ├── src/
│   │   ├── api/axios.js        # Axios instance configured for FastAPI
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx   # Sales KPIs & Recharts visualizations
│   │   │   ├── Customers.jsx   # Customer table, search, filters & order history modal
│   │   │   ├── Products.jsx    # Products catalog, inventory, and revenues
│   │   │   ├── Orders.jsx      # Order transactions and status filters
│   │   │   ├── Upload.jsx      # CSV drag-and-drop & duplicate hash detection
│   │   │   └── ETLMonitor.jsx  # Pipeline trigger, live logs & rejected rows inspector
│   │   ├── App.jsx             # Sidebar navigation & React Router
│   │   └── index.css           # Tailwind CSS directives
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

---

## 💾 Database Schema (7 Tables)

1. **`customers`**: Stores verified customer profiles (`customer_id`, `name`, `email` [UNIQUE], `city`, `country`, `signup_date`).
2. **`products`**: Product catalog (`product_id`, `name`, `category`, `unit_price` [CHECK > 0], `stock`).
3. **`orders`**: Sales transactions (`order_id`, `customer_id` [FK], `product_id` [FK], `quantity` [CHECK > 0], `unit_price`, `discount_pct`, `total_amount`, `status`).
4. **`uploaded_files`**: Tracks every uploaded file with SHA-256 file hashes to prevent duplicate ingestion.
5. **`etl_runs`**: Records batch execution metadata (status, rows read, inserted, updated, rejected, duration).
6. **`etl_logs`**: Step-by-step logs (`INFO`, `WARNING`, `ERROR`) emitted during pipeline runs.
7. **`rejected_records`**: Quarantines dirty records along with exact failure reasons and raw JSON input.

---

## ⚡ Setup & Execution Guide

### 1. Database Setup
Ensure PostgreSQL is running locally and create the database:
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

# Configure .env file
# Create a .env file with your PostgreSQL credentials:
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=sales_analytics
# DB_USER=postgres
# DB_PASSWORD=your_password 
# UPLOAD_DIR=uploads

# Start FastAPI server
uvicorn main:app --reload
```
API Documentation will be live at: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
Open a new terminal:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```
Dashboard will be live at: `http://localhost:5173/`

---

## 🧪 Testing the Complete Workflow
1. Navigate to **📁 Upload CSV** in the web interface.
2. Upload `sample_data/customers.csv`, `products.csv`, and `orders.csv`. Notice:
   - Uploading the exact same file twice flags it as a duplicate via SHA-256 hash.
3. Navigate to **⚙️ ETL Monitor** and click **🚀 Trigger Pipeline**:
   - Live logs display in real time.
   - Inspect the **Quarantined Rejected Records** tab to see invalid rows (e.g. invalid email format, negative prices, orphan customer keys) caught cleanly without breaking the batch.
4. Navigate to **📊 Dashboard** to view calculated real-time KPIs and interactive charts powered by live PostgreSQL queries.