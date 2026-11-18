from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/data", tags=["Data"])


# ─────────────────────────────────────────────
# CUSTOMERS TABLE
# ─────────────────────────────────────────────

@router.get("/customers")
def get_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    country: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Paginated customers list.
    Optional filters: search (name/email), country
    """
    offset = (page - 1) * limit
    filters = []
    params = {"limit": limit, "offset": offset}

    if search:
        filters.append("(c.name ILIKE :search OR c.email ILIKE :search)")
        params["search"] = f"%{search}%"

    if country:
        filters.append("c.country = :country")
        params["country"] = country

    where = "WHERE " + " AND ".join(filters) if filters else ""

    # Total count for pagination
    total = db.execute(text(f"""
        SELECT COUNT(*) FROM customers c {where}
    """), params).scalar()

    # Fetch customers with their order stats
    rows = db.execute(text(f"""
        SELECT
            c.customer_id,
            c.name,
            c.email,
            c.city,
            c.country,
            c.signup_date,
            COUNT(o.order_id)       AS total_orders,
            COALESCE(SUM(o.total_amount), 0) AS total_spent
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
            AND o.status IN ('completed', 'shipped')
        {where}
        GROUP BY c.customer_id, c.name, c.email,
                 c.city, c.country, c.signup_date
        ORDER BY total_spent DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    return {
        "total":   total,
        "page":    page,
        "limit":   limit,
        "pages":   (total + limit - 1) // limit,
        "data":    [dict(row._mapping) for row in rows]
    }


# ─────────────────────────────────────────────
# SINGLE CUSTOMER DETAIL
# ─────────────────────────────────────────────

@router.get("/customers/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Full detail for a single customer including their orders."""
    customer = db.execute(text("""
        SELECT
            c.*,
            COUNT(o.order_id)               AS total_orders,
            COALESCE(SUM(o.total_amount),0) AS total_spent,
            MAX(o.order_date)               AS last_order_date
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        WHERE c.customer_id = :customer_id
        GROUP BY c.customer_id
    """), {"customer_id": customer_id}).fetchone()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Get their orders
    orders = db.execute(text("""
        SELECT
            o.order_id,
            p.name      AS product_name,
            p.category,
            o.quantity,
            o.total_amount,
            o.status,
            o.order_date
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        WHERE o.customer_id = :customer_id
        ORDER BY o.order_date DESC
    """), {"customer_id": customer_id}).fetchall()

    return {
        "customer": dict(customer._mapping),
        "orders":   [dict(row._mapping) for row in orders]
    }


# ─────────────────────────────────────────────
# PRODUCTS TABLE
# ─────────────────────────────────────────────

@router.get("/products")
def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    category: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Paginated products list.
    Optional filters: search (name), category
    """
    offset = (page - 1) * limit
    filters = []
    params = {"limit": limit, "offset": offset}

    if search:
        filters.append("p.name ILIKE :search")
        params["search"] = f"%{search}%"

    if category:
        filters.append("p.category = :category")
        params["category"] = category

    where = "WHERE " + " AND ".join(filters) if filters else ""

    total = db.execute(text(f"""
        SELECT COUNT(*) FROM products p {where}
    """), params).scalar()

    rows = db.execute(text(f"""
        SELECT
            p.product_id,
            p.name,
            p.category,
            p.unit_price,
            p.stock,
            COUNT(o.order_id)               AS total_orders,
            COALESCE(SUM(o.quantity), 0)    AS total_sold,
            COALESCE(SUM(o.total_amount),0) AS total_revenue
        FROM products p
        LEFT JOIN orders o ON p.product_id = o.product_id
            AND o.status IN ('completed','shipped')
        {where}
        GROUP BY p.product_id, p.name, p.category,
                 p.unit_price, p.stock
        ORDER BY total_revenue DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    return {
        "total": total,
        "page":  page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "data":  [dict(row._mapping) for row in rows]
    }


# ─────────────────────────────────────────────
# ORDERS TABLE
# ─────────────────────────────────────────────

@router.get("/orders")
def get_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    customer_id: str = Query(None),
    product_id: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Paginated orders list with customer and product names.
    Optional filters: status, customer_id, product_id
    """
    offset = (page - 1) * limit
    filters = []
    params = {"limit": limit, "offset": offset}

    VALID_STATUSES = {"completed", "shipped", "pending", "cancelled", "returned"}

    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        filters.append("o.status = :status")
        params["status"] = status

    if customer_id:
        filters.append("o.customer_id = :customer_id")
        params["customer_id"] = customer_id

    if product_id:
        filters.append("o.product_id = :product_id")
        params["product_id"] = product_id

    where = "WHERE " + " AND ".join(filters) if filters else ""

    total = db.execute(text(f"""
        SELECT COUNT(*) FROM orders o {where}
    """), params).scalar()

    rows = db.execute(text(f"""
        SELECT
            o.order_id,
            o.customer_id,
            c.name          AS customer_name,
            o.product_id,
            p.name          AS product_name,
            p.category,
            o.quantity,
            o.unit_price,
            o.discount_pct,
            o.total_amount,
            o.status,
            o.order_date
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN products  p ON o.product_id  = p.product_id
        {where}
        ORDER BY o.order_date DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    return {
        "total": total,
        "page":  page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "data":  [dict(row._mapping) for row in rows]
    }


# ─────────────────────────────────────────────
# FILTER OPTIONS (for dropdowns)
# ─────────────────────────────────────────────

@router.get("/filters")
def get_filter_options(db: Session = Depends(get_db)):
    """
    Returns unique values for filter dropdowns:
    - countries, categories, statuses
    """
    countries = db.execute(text("""
        SELECT DISTINCT country FROM customers
        ORDER BY country
    """)).fetchall()

    categories = db.execute(text("""
        SELECT DISTINCT category FROM products
        ORDER BY category
    """)).fetchall()

    statuses = db.execute(text("""
        SELECT DISTINCT status FROM orders
        ORDER BY status
    """)).fetchall()

    return {
        "countries":  [row[0] for row in countries],
        "categories": [row[0] for row in categories],
        "statuses":   [row[0] for row in statuses]
    }