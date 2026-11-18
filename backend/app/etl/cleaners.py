import pandas as pd
import numpy as np
import re
from datetime import datetime

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def is_valid_email(email: str) -> bool:
    """Check if email matches standard format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    return bool(re.match(pattern, str(email).strip()))

def clean_string(value) -> str:
    """Strip whitespace and normalize a string value."""
    if pd.isna(value):
        return ""
    return str(value).strip()

def reject_row(rejected: list, row_index: int, row: pd.Series, reason: str):
    """Add a row to the rejected list with its reason."""
    rejected.append({
        "row_number": row_index + 2,  # +2 because index starts at 0 and CSV has header
        "reason": reason,
        "raw_data": row.to_dict()
    })

# ─────────────────────────────────────────────
# CUSTOMERS CLEANER
# ─────────────────────────────────────────────

def clean_customers(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """
    Validate and clean the customers dataframe.
    Returns: (clean_df, rejected_rows)
    """
    clean_rows = []
    rejected = []

    # Normalize column names: lowercase and strip spaces
    df.columns = df.columns.str.strip().str.lower()

    for idx, row in df.iterrows():
        customer_id = clean_string(row.get("customer_id", ""))
        name        = clean_string(row.get("name", ""))
        email       = clean_string(row.get("email", ""))
        city        = clean_string(row.get("city", "")) or "Unknown"
        country     = clean_string(row.get("country", "")) or "Unknown"
        signup_date = clean_string(row.get("signup_date", ""))

        # ── Validations ──────────────────────────────
        if not customer_id:
            reject_row(rejected, idx, row, "Missing customer_id")
            continue

        if not name:
            reject_row(rejected, idx, row, "Missing name")
            continue

        if not email:
            reject_row(rejected, idx, row, "Missing email")
            continue

        if not is_valid_email(email):
            reject_row(rejected, idx, row, f"Invalid email format: {email}")
            continue

        # Parse signup_date if present
        parsed_date = None
        if signup_date:
            try:
                parsed_date = pd.to_datetime(signup_date).date()
            except Exception:
                reject_row(rejected, idx, row, f"Invalid signup_date: {signup_date}")
                continue

        # ── All checks passed ────────────────────────
        clean_rows.append({
            "customer_id": customer_id,
            "name":        name,
            "email":       email.lower(),
            "city":        city,
            "country":     country,
            "signup_date": parsed_date
        })

    clean_df = pd.DataFrame(clean_rows)
    return clean_df, rejected


# ─────────────────────────────────────────────
# PRODUCTS CLEANER
# ─────────────────────────────────────────────

def clean_products(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """
    Validate and clean the products dataframe.
    Returns: (clean_df, rejected_rows)
    """
    clean_rows = []
    rejected = []

    df.columns = df.columns.str.strip().str.lower()

    for idx, row in df.iterrows():
        product_id = clean_string(row.get("product_id", ""))
        name       = clean_string(row.get("name", ""))
        category   = clean_string(row.get("category", "")) or "Uncategorized"
        stock      = row.get("stock", 0)

        # ── Validate unit_price ──────────────────────
        try:
            unit_price = float(row.get("unit_price", 0))
        except (ValueError, TypeError):
            reject_row(rejected, idx, row, f"Invalid unit_price: {row.get('unit_price')}")
            continue

        # ── Validations ──────────────────────────────
        if not product_id:
            reject_row(rejected, idx, row, "Missing product_id")
            continue

        if not name:
            reject_row(rejected, idx, row, "Missing name")
            continue

        if unit_price <= 0:
            reject_row(rejected, idx, row, f"unit_price must be > 0, got: {unit_price}")
            continue

        # ── Validate stock ───────────────────────────
        try:
            stock = int(stock)
            if stock < 0:
                reject_row(rejected, idx, row, f"stock cannot be negative: {stock}")
                continue
        except (ValueError, TypeError):
            stock = 0  # default to 0 if missing

        # ── All checks passed ────────────────────────
        clean_rows.append({
            "product_id": product_id,
            "name":       name,
            "category":   category,
            "unit_price": round(unit_price, 2),
            "stock":      stock
        })

    clean_df = pd.DataFrame(clean_rows)
    return clean_df, rejected


# ─────────────────────────────────────────────
# ORDERS CLEANER
# ─────────────────────────────────────────────

def clean_orders(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """
    Validate and clean the orders dataframe.
    Returns: (clean_df, rejected_rows)
    """
    clean_rows = []
    rejected = []

    VALID_STATUSES = {"completed", "shipped", "pending", "cancelled", "returned"}

    df.columns = df.columns.str.strip().str.lower()

    for idx, row in df.iterrows():
        order_id    = clean_string(row.get("order_id", ""))
        customer_id = clean_string(row.get("customer_id", ""))
        product_id  = clean_string(row.get("product_id", ""))
        order_date  = clean_string(row.get("order_date", ""))
        status      = clean_string(row.get("status", "pending")).lower()

        # ── Validate required IDs ────────────────────
        if not order_id:
            reject_row(rejected, idx, row, "Missing order_id")
            continue

        if not customer_id:
            reject_row(rejected, idx, row, "Missing customer_id")
            continue

        if not product_id:
            reject_row(rejected, idx, row, "Missing product_id")
            continue

        # ── Validate quantity ────────────────────────
        try:
            quantity = int(row.get("quantity", 0))
            if quantity <= 0:
                reject_row(rejected, idx, row, f"quantity must be > 0, got: {quantity}")
                continue
        except (ValueError, TypeError):
            reject_row(rejected, idx, row, f"Invalid quantity: {row.get('quantity')}")
            continue

        # ── Validate unit_price ──────────────────────
        try:
            unit_price = float(row.get("unit_price", 0))
            if unit_price < 0:
                reject_row(rejected, idx, row, f"unit_price cannot be negative: {unit_price}")
                continue
        except (ValueError, TypeError):
            reject_row(rejected, idx, row, f"Invalid unit_price: {row.get('unit_price')}")
            continue

        # ── Validate discount_pct ────────────────────
        try:
            discount_pct = float(row.get("discount_pct", 0))
            if not (0 <= discount_pct <= 100):
                reject_row(rejected, idx, row, f"discount_pct must be 0-100, got: {discount_pct}")
                continue
        except (ValueError, TypeError):
            discount_pct = 0.0

        # ── Validate status ──────────────────────────
        if status not in VALID_STATUSES:
            reject_row(rejected, idx, row, f"Invalid status: {status}")
            continue

        # ── Validate order_date ──────────────────────
        try:
            parsed_date = pd.to_datetime(order_date).date()
        except Exception:
            reject_row(rejected, idx, row, f"Invalid order_date: {order_date}")
            continue

        # ── Calculate total_amount ───────────────────
        total_amount = round(quantity * unit_price * (1 - discount_pct / 100), 2)

        # ── All checks passed ────────────────────────
        clean_rows.append({
            "order_id":     order_id,
            "customer_id":  customer_id,
            "product_id":   product_id,
            "quantity":     quantity,
            "unit_price":   round(unit_price, 2),
            "discount_pct": round(discount_pct, 2),
            "total_amount": total_amount,
            "order_date":   parsed_date,
            "status":       status
        })

    clean_df = pd.DataFrame(clean_rows)
    return clean_df, rejected


# ─────────────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────────────

def clean_dataframe(entity: str, df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """
    Route to the correct cleaner based on entity type.
    """
    if entity == "customers":
        return clean_customers(df)
    elif entity == "products":
        return clean_products(df)
    elif entity == "orders":
        return clean_orders(df)
    else:
        raise ValueError(f"Unknown entity: {entity}")