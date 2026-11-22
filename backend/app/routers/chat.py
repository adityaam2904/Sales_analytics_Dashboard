# import os
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from sqlalchemy import text
# from pydantic import BaseModel
# from app.database import get_db
# from google import genai
# from dotenv import load_dotenv

# load_dotenv()

# router = APIRouter(prefix="/chat", tags=["AI Chatbot"])

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# class ChatRequest(BaseModel):
#     question: str

# # ─────────────────────────────────────────────
# # FETCH LIVE CONTEXT FROM POSTGRESQL
# # ─────────────────────────────────────────────

# def build_data_context(db: Session) -> str:
#     """
#     Queries PostgreSQL to gather live business data
#     and formats it as a readable text context for Gemini.
#     """
#     context_parts = []

#     # 1. KPI Summary
#     try:
#         kpis = db.execute(text("""
#             SELECT
#                 COUNT(DISTINCT o.order_id)                      AS total_orders,
#                 COUNT(DISTINCT o.customer_id)                   AS active_customers,
#                 COUNT(DISTINCT c.customer_id)                   AS total_customers,
#                 COUNT(DISTINCT p.product_id)                    AS total_products,
#                 COALESCE(SUM(CASE WHEN o.status IN 
#                     ('completed','shipped') THEN o.total_amount ELSE 0 END), 0) AS total_revenue,
#                 COALESCE(AVG(CASE WHEN o.status IN 
#                     ('completed','shipped') THEN o.total_amount END), 0) AS avg_order_value,
#                 COUNT(CASE WHEN o.status = 'cancelled' THEN 1 END) AS cancelled_orders,
#                 COUNT(CASE WHEN o.status = 'returned' THEN 1 END)  AS returned_orders
#             FROM customers c
#             LEFT JOIN orders o ON c.customer_id = o.customer_id
#             LEFT JOIN products p ON o.product_id = p.product_id
#         """)).fetchone()

#         if kpis:
#             context_parts.append(f"""
# 📊 BUSINESS KPI SUMMARY:
# - Total Revenue (completed & shipped): ${float(kpis.total_revenue):,.2f}
# - Average Order Value: ${float(kpis.avg_order_value):,.2f}
# - Total Orders: {kpis.total_orders}
# - Total Customers: {kpis.total_customers}
# - Active Customers (with orders): {kpis.active_customers}
# - Total Products: {kpis.total_products}
# - Cancelled Orders: {kpis.cancelled_orders}
# - Returned Orders: {kpis.returned_orders}
# """)
#     except Exception as e:
#         print(f"Error fetching KPIs: {e}")

#     # 2. Top 5 Customers
#     try:
#         top_customers = db.execute(text("""
#             SELECT c.name, COUNT(o.order_id) AS total_orders,
#                    SUM(o.total_amount) AS total_spent
#             FROM customers c
#             JOIN orders o ON c.customer_id = o.customer_id
#             WHERE o.status IN ('completed','shipped')
#             GROUP BY c.name
#             ORDER BY total_spent DESC
#             LIMIT 5
#         """)).fetchall()

#         if top_customers:
#             context_parts.append("🏆 TOP 5 CUSTOMERS BY REVENUE:")
#             for i, row in enumerate(top_customers, 1):
#                 context_parts.append(
#                     f"  {i}. {row.name} — ${float(row.total_spent):,.2f} "
#                     f"({row.total_orders} orders)"
#                 )
#             context_parts.append("")
#     except Exception as e:
#         print(f"Error fetching top customers: {e}")

#     # 3. Top 5 Products
#     try:
#         top_products = db.execute(text("""
#             SELECT p.name, p.category,
#                    SUM(o.quantity) AS total_sold,
#                    SUM(o.total_amount) AS total_revenue
#             FROM products p
#             JOIN orders o ON p.product_id = o.product_id
#             WHERE o.status IN ('completed','shipped')
#             GROUP BY p.name, p.category
#             ORDER BY total_revenue DESC
#             LIMIT 5
#         """)).fetchall()

#         if top_products:
#             context_parts.append("📦 TOP 5 PRODUCTS BY REVENUE:")
#             for i, row in enumerate(top_products, 1):
#                 context_parts.append(
#                     f"  {i}. {row.name} ({row.category}) — "
#                     f"${float(row.total_revenue):,.2f} | {row.total_sold} units sold"
#                 )
#             context_parts.append("")
#     except Exception as e:
#         print(f"Error fetching top products: {e}")

#     # 4. Revenue by Category
#     try:
#         categories = db.execute(text("""
#             SELECT p.category, SUM(o.total_amount) AS revenue,
#                    ROUND(100.0 * SUM(o.total_amount) /
#                    NULLIF(SUM(SUM(o.total_amount)) OVER (), 0), 2) AS pct
#             FROM orders o
#             JOIN products p ON o.product_id = p.product_id
#             WHERE o.status IN ('completed','shipped')
#             GROUP BY p.category
#             ORDER BY revenue DESC
#         """)).fetchall()

#         if categories:
#             context_parts.append("📂 REVENUE BY CATEGORY:")
#             for row in categories:
#                 context_parts.append(
#                     f"  - {row.category}: ${float(row.revenue):,.2f} ({row.pct}%)"
#                 )
#             context_parts.append("")
#     except Exception as e:
#         print(f"Error fetching categories: {e}")

#     return "\n".join(context_parts) if context_parts else "No business data available in database yet."


# # ─────────────────────────────────────────────
# # CHAT ENDPOINT
# # ─────────────────────────────────────────────

# @router.post("/ask")
# async def ask_chatbot(request: ChatRequest, db: Session = Depends(get_db)):
#     """
#     Accepts user question, fetches live PostgreSQL context,
#     and returns Gemini's natural response.
#     """
#     if not GEMINI_API_KEY:
#         raise HTTPException(
#             status_code=500,
#             detail="Gemini API key not configured. Please add GEMINI_API_KEY to your .env file."
#         )

#     if not request.question or not request.question.strip():
#         raise HTTPException(status_code=400, detail="Question cannot be empty.")

#     # 1. Fetch live PostgreSQL data
#     data_context = build_data_context(db)

#     # 2. Build system instruction & prompt
#     prompt = f"""You are an expert AI Sales Analytics Assistant for a company's data dashboard.

# Here is the LIVE business data queried directly from the PostgreSQL database:
# ----------------------------------------
# {data_context}
# ----------------------------------------

# User Question: "{request.question.strip()}"

# Instructions:
# - Answer accurately based on the database numbers provided above.
# - Use actual numbers, customer names, and product names when relevant.
# - Format money values nicely (e.g. $1,250.00).
# - Be concise and professional (under 150 words).
# - If the question cannot be answered from the provided data, state that clearly and politely.
# """

#     # 3. Call modern Google GenAI Client
#         # 3. Call Google GenAI Client with auto-fallback
#     client = genai.Client(api_key=GEMINI_API_KEY)
    
#     # Try the recommended models in priority order
#     candidate_models = ["gemini-3.5-flash-lite", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
#     answer = None
#     last_error = None

#     for model_name in candidate_models:
#         try:
#             response = client.models.generate_content(
#                 model=model_name,
#                 contents=prompt
#             )
#             if response and response.text:
#                 answer = response.text
#                 break
#         except Exception as e:
#             last_error = e
#             print(f"Model {model_name} busy or failed: {e}. Trying next fallback...")
#             continue

#     if not answer:
#         raise HTTPException(
#             status_code=503,
#             detail=f"AI service temporarily busy across all models. Details: {str(last_error)}"
#         )
#     return {
#         "question": request.question,
#         "answer": answer,
#         "data_context_used": True
#     }


# @router.get("/health")
# def chat_health():
#     """Check if Gemini API key is configured."""
#     return {
#         "gemini_configured": bool(GEMINI_API_KEY),
#         "status": "ready" if GEMINI_API_KEY else "missing_api_key"
#     }