import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

# ─────────────────────────────────────────────
# CUSTOMERS LOADER
# ─────────────────────────────────────────────

def load_customers(df: pd.DataFrame, db: Session) -> dict:
    """
    Upsert customers into PostgreSQL.
    - If customer_id exists → update name, email, city, country, signup_date
- If customer_id is new → insert
    """
    inserted = updated = unchanged = 0

    for _, row in df.iterrows():
        # Check if customer already exists
        existing = db.execute(text("""
            SELECT customer_id, name, email, city, country
            FROM customers
            WHERE customer_id = :customer_id
        """), {"customer_id": row["customer_id"]}).fetchone()

        if existing is None:
            # INSERT new customer
            db.execute(text("""
                INSERT INTO customers
                    (customer_id, name, email, city, country, signup_date)
                VALUES
                    (:customer_id, :name, :email, :city, :country, :signup_date)
            """), {
                "customer_id": row["customer_id"],
                "name":        row["name"],
                "email":       row["email"],
                "city":        row["city"],
                "country":     row["country"],
                "signup_date": row.get("signup_date")
            })
            inserted += 1

        else:
            # Check if anything actually changed
            if (existing.name    != row["name"]    or
                existing.email   != row["email"]   or
                existing.city    != row["city"]    or
                existing.country != row["country"]):

                # UPDATE existing customer
                db.execute(text("""
                    UPDATE customers
                    SET name        = :name,
                        email       = :email,
                        city        = :city,
                        country     = :country,
                        signup_date = :signup_date,
                        updated_at  = now()
                    WHERE customer_id = :customer_id
                """), {
                    "customer_id": row["customer_id"],
                    "name":        row["name"],
                    "email":       row["email"],
                    "city":        row["city"],
                    "country":     row["country"],
                    "signup_date": row.get("signup_date")
                })
                updated += 1
            else:
                unchanged += 1

    db.commit()
    return {"inserted": inserted, "updated": updated, "unchanged": unchanged}


# ─────────────────────────────────────────────
# PRODUCTS LOADER
# ─────────────────────────────────────────────

def load_products(df: pd.DataFrame, db: Session) -> dict:
    """
    Upsert products into PostgreSQL.
    - If product_id exists → update name, category, unit_price, stock
    - If product_id is new → insert
    """
    inserted = updated = unchanged = 0

    for _, row in df.iterrows():
        existing = db.execute(text("""
            SELECT product_id, name, category, unit_price, stock
            FROM products
            WHERE product_id = :product_id
        """), {"product_id": row["product_id"]}).fetchone()

        if existing is None:
            db.execute(text("""
                INSERT INTO products
                    (product_id, name, category, unit_price, stock)
                VALUES
                    (:product_id, :name, :category, :unit_price, :stock)
            """), {
                "product_id": row["product_id"],
                "name":       row["name"],
                "category":   row["category"],
                "unit_price": row["unit_price"],
                "stock":      row["stock"]
            })
            inserted += 1

        else:
            if (existing.name       != row["name"]       or
                existing.category   != row["category"]   or
                float(existing.unit_price) != float(row["unit_price"]) or
                existing.stock      != row["stock"]):

                db.execute(text("""
                    UPDATE products
                    SET name       = :name,
                        category   = :category,
                        unit_price = :unit_price,
                        stock      = :stock,
                        updated_at = now()
                    WHERE product_id = :product_id
                """), {
                    "product_id": row["product_id"],
                    "name":       row["name"],
                    "category":   row["category"],
                    "unit_price": row["unit_price"],
                    "stock":      row["stock"]
                })
                updated += 1
            else:
                unchanged += 1

    db.commit()
    return {"inserted": inserted, "updated": updated, "unchanged": unchanged}


# ─────────────────────────────────────────────
# ORDERS LOADER
# ─────────────────────────────────────────────

def load_orders(df: pd.DataFrame, db: Session) -> dict:
    """
    Upsert orders into PostgreSQL.
    - Skips orders whose customer_id or product_id doesn't exist in DB
    - If order_id exists → update status and amounts
    - If order_id is new → insert
    Returns counts + list of skipped (orphan) rows.
    """
    inserted = updated = unchanged = 0
    skipped = []

    # Fetch valid customer and product IDs from DB for fast lookup
    valid_customers = set(
        row[0] for row in db.execute(text("SELECT customer_id FROM customers")).fetchall()
    )
    valid_products = set(
        row[0] for row in db.execute(text("SELECT product_id FROM products")).fetchall()
    )

    for _, row in df.iterrows():
        # Foreign key validation before insert
        if row["customer_id"] not in valid_customers:
            skipped.append({
                "row": row.to_dict(),
                "reason": f"customer_id '{row['customer_id']}' does not exist in customers table"
            })
            continue

        if row["product_id"] not in valid_products:
            skipped.append({
                "row": row.to_dict(),
                "reason": f"product_id '{row['product_id']}' does not exist in products table"
            })
            continue

        existing = db.execute(text("""
            SELECT order_id, status, total_amount
            FROM orders
            WHERE order_id = :order_id
        """), {"order_id": row["order_id"]}).fetchone()

        if existing is None:
            db.execute(text("""
                INSERT INTO orders
                    (order_id, customer_id, product_id, quantity,
                     unit_price, discount_pct, total_amount,
                     order_date, status)
                VALUES
                    (:order_id, :customer_id, :product_id, :quantity,
                     :unit_price, :discount_pct, :total_amount,
                     :order_date, :status)
            """), {
                "order_id":     row["order_id"],
                "customer_id":  row["customer_id"],
                "product_id":   row["product_id"],
                "quantity":     row["quantity"],
                "unit_price":   row["unit_price"],
                "discount_pct": row["discount_pct"],
                "total_amount": row["total_amount"],
                "order_date":   row["order_date"],
                "status":       row["status"]
            })
            inserted += 1

        else:
            if (existing.status != row["status"] or
                float(existing.total_amount) != float(row["total_amount"])):

                db.execute(text("""
                    UPDATE orders
                    SET status       = :status,
                        total_amount = :total_amount,
                        updated_at   = now()
                    WHERE order_id = :order_id
                """), {
                    "order_id":     row["order_id"],
                    "status":       row["status"],
                    "total_amount": row["total_amount"]
                })
                updated += 1
            else:
                unchanged += 1

    db.commit()
    return {
        "inserted":  inserted,
        "updated":   updated,
        "unchanged": unchanged,
        "skipped":   skipped
    }


# ─────────────────────────────────────────────
# REJECTED RECORDS SAVER
# ─────────────────────────────────────────────

def save_rejected_records(
    rejected: list,
    entity: str,
    run_id: int,
    upload_id: int,
    db: Session
):
    """Save all rejected rows into the rejected_records table."""
    import json

    for record in rejected:
        try:
            db.execute(text("""
                INSERT INTO rejected_records
                    (run_id, upload_id, entity, row_number, reason, raw_data)
                VALUES
                    (:run_id, :upload_id, :entity, :row_number, :reason, :raw_data)
                ON CONFLICT (upload_id, row_number) DO NOTHING
            """), {
                "run_id":     run_id,
                "upload_id":  upload_id,
                "entity":     entity,
                "row_number": record["row_number"],
                "reason":     record["reason"],
                "raw_data":   json.dumps(record["raw_data"], default=str)
            })
        except Exception:
            continue

    db.commit()


# ─────────────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────────────

def load_dataframe(entity: str, df: pd.DataFrame, db: Session) -> dict:
    """Route to the correct loader based on entity type."""
    if entity == "customers":
        return load_customers(df, db)
    elif entity == "products":
        return load_products(df, db)
    elif entity == "orders":
        return load_orders(df, db)
    else:
        raise ValueError(f"Unknown entity: {entity}")