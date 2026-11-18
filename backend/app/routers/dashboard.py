from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ─────────────────────────────────────────────
# KPI OVERVIEW CARDS
# ─────────────────────────────────────────────

@router.get("/kpis")
def get_kpis(db: Session = Depends(get_db)):
    """
    Returns top-level KPI metrics for the dashboard overview:
    - Total revenue
    - Total orders
    - Total customers
    - Average order value
    - Total products
    - Cancelled / returned rate
    """
    result = db.execute(text("""
        SELECT
            COUNT(DISTINCT o.order_id)                          AS total_orders,
            COUNT(DISTINCT o.customer_id)                       AS active_customers,
            COUNT(DISTINCT c.customer_id)                       AS total_customers,
            COUNT(DISTINCT o.product_id)                        AS total_products,
            COALESCE(SUM(
                CASE WHEN o.status IN ('completed','shipped')
                THEN o.total_amount ELSE 0 END), 0)             AS total_revenue,
            COALESCE(AVG(
                CASE WHEN o.status IN ('completed','shipped')
                THEN o.total_amount END), 0)                    AS avg_order_value,
            COUNT(CASE WHEN o.status = 'cancelled' THEN 1 END)  AS cancelled_orders,
            COUNT(CASE WHEN o.status = 'returned'  THEN 1 END)  AS returned_orders
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
    """)).fetchone()

    return dict(result._mapping)


# ─────────────────────────────────────────────
# MONTHLY REVENUE TREND
# ─────────────────────────────────────────────

@router.get("/monthly-revenue")
def get_monthly_revenue(db: Session = Depends(get_db)):
    """
    Monthly revenue and order count for the last 12 months.
    Used for the line/bar chart on the dashboard.
    """
    rows = db.execute(text("""
        SELECT
            TO_CHAR(order_date, 'YYYY-MM')          AS month,
            COUNT(order_id)                          AS total_orders,
            SUM(total_amount)                        AS revenue,
            AVG(total_amount)                        AS avg_order_value
        FROM orders
        WHERE status IN ('completed', 'shipped')
          AND order_date >= NOW() - INTERVAL '12 months'
        GROUP BY TO_CHAR(order_date, 'YYYY-MM')
        ORDER BY month ASC
    """)).fetchall()

    return [dict(row._mapping) for row in rows]


# ─────────────────────────────────────────────
# REVENUE BY CATEGORY
# ─────────────────────────────────────────────

@router.get("/revenue-by-category")
def get_revenue_by_category(db: Session = Depends(get_db)):
    """
    Total revenue grouped by product category.
    Used for the pie/donut chart.
    """
    rows = db.execute(text("""
        SELECT
            p.category,
            COUNT(o.order_id)       AS total_orders,
            SUM(o.total_amount)     AS revenue,
            ROUND(
                100.0 * SUM(o.total_amount) /
                NULLIF(SUM(SUM(o.total_amount)) OVER (), 0)
            , 2)                    AS revenue_pct
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        WHERE o.status IN ('completed', 'shipped')
        GROUP BY p.category
        ORDER BY revenue DESC
    """)).fetchall()

    return [dict(row._mapping) for row in rows]


# ─────────────────────────────────────────────
# TOP PRODUCTS
# ─────────────────────────────────────────────

@router.get("/top-products")
def get_top_products(limit: int = 10, db: Session = Depends(get_db)):
    """
    Top N products by revenue with quantity sold and order count.
    """
    rows = db.execute(text("""
        SELECT
            p.product_id,
            p.name                      AS product_name,
            p.category,
            COUNT(o.order_id)           AS total_orders,
            SUM(o.quantity)             AS total_quantity_sold,
            SUM(o.total_amount)         AS total_revenue,
            AVG(o.discount_pct)         AS avg_discount,
            RANK() OVER (
                ORDER BY SUM(o.total_amount) DESC
            )                           AS revenue_rank
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        WHERE o.status IN ('completed', 'shipped')
        GROUP BY p.product_id, p.name, p.category
        ORDER BY total_revenue DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [dict(row._mapping) for row in rows]


# ─────────────────────────────────────────────
# TOP CUSTOMERS
# ─────────────────────────────────────────────

@router.get("/top-customers")
def get_top_customers(limit: int = 10, db: Session = Depends(get_db)):
    """
    Top N customers by total spend using window functions.
    """
    rows = db.execute(text("""
        WITH customer_stats AS (
            SELECT
                c.customer_id,
                c.name,
                c.email,
                c.city,
                c.country,
                COUNT(o.order_id)       AS total_orders,
                SUM(o.total_amount)     AS total_spent,
                AVG(o.total_amount)     AS avg_order_value,
                MIN(o.order_date)       AS first_order_date,
                MAX(o.order_date)       AS last_order_date
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE o.status IN ('completed', 'shipped')
            GROUP BY c.customer_id, c.name, c.email, c.city, c.country
        )
        SELECT
            *,
            RANK() OVER (ORDER BY total_spent DESC)  AS spending_rank
        FROM customer_stats
        ORDER BY total_spent DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [dict(row._mapping) for row in rows]


# ─────────────────────────────────────────────
# ORDER STATUS BREAKDOWN
# ─────────────────────────────────────────────

@router.get("/order-status")
def get_order_status(db: Session = Depends(get_db)):
    """
    Count of orders grouped by status.
    Used for pie/donut chart.
    """
    rows = db.execute(text("""
        SELECT
            status,
            COUNT(order_id)     AS total_orders,
            SUM(total_amount)   AS total_amount,
            ROUND(
                100.0 * COUNT(order_id) /
                NULLIF(SUM(COUNT(order_id)) OVER (), 0)
            , 2)                AS percentage
        FROM orders
        GROUP BY status
        ORDER BY total_orders DESC
    """)).fetchall()

    return [dict(row._mapping) for row in rows]


# ─────────────────────────────────────────────
# SALES BY COUNTRY
# ─────────────────────────────────────────────

@router.get("/sales-by-country")
def get_sales_by_country(db: Session = Depends(get_db)):
    """
    Revenue and order count grouped by customer country.
    """
    rows = db.execute(text("""
        SELECT
            c.country,
            COUNT(DISTINCT c.customer_id)   AS total_customers,
            COUNT(o.order_id)               AS total_orders,
            SUM(o.total_amount)             AS total_revenue
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        WHERE o.status IN ('completed', 'shipped')
        GROUP BY c.country
        ORDER BY total_revenue DESC
    """)).fetchall()

    return [dict(row._mapping) for row in rows]


# ─────────────────────────────────────────────
# RECENT ORDERS
# ─────────────────────────────────────────────

@router.get("/recent-orders")
def get_recent_orders(limit: int = 10, db: Session = Depends(get_db)):
    """
    Most recent orders with customer and product names.
    """
    rows = db.execute(text("""
        SELECT
            o.order_id,
            c.name          AS customer_name,
            p.name          AS product_name,
            p.category,
            o.quantity,
            o.total_amount,
            o.status,
            o.order_date
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN products  p ON o.product_id  = p.product_id
        ORDER BY o.order_date DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [dict(row._mapping) for row in rows]