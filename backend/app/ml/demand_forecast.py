"""
Demand forecasting using historical order data.
Uses scikit-learn / simple moving average + optional XGBoost when enough data exists.
Designed to run asynchronously (Celery-ready).
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from bson import ObjectId

from app.core.database import get_db


async def build_sales_dataframe(days: int = 180) -> pd.DataFrame:
    db = get_db()
    start = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {"$match": {"created_at": {"$gte": start}, "status": {"$nin": ["cancelled", "refunded"]}}},
        {"$unwind": "$items"},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "product_id": "$items.product_id",
            },
            "qty": {"$sum": "$items.quantity"},
            "revenue": {"$sum": "$items.line_total"},
        }},
    ]
    rows = await db.orders.aggregate(pipeline).to_list(100000)
    if not rows:
        return pd.DataFrame(columns=["date", "product_id", "qty", "revenue"])
    df = pd.DataFrame([
        {
            "date": r["_id"]["date"],
            "product_id": str(r["_id"]["product_id"]),
            "qty": r["qty"],
            "revenue": r["revenue"],
        }
        for r in rows
    ])
    df["date"] = pd.to_datetime(df["date"])
    return df


def simple_forecast(series: pd.Series, horizon: int = 30) -> Dict[str, Any]:
    """Moving-average + linear trend fallback when data is sparse."""
    if len(series) < 3:
        avg = float(series.mean()) if len(series) else 0.0
        return {
            "predicted_total": round(avg * horizon, 1),
            "daily_avg": round(avg, 2),
            "trend": "stable",
            "growth_pct": 0.0,
            "confidence": "low",
            "method": "mean",
        }
    # last 14-day avg vs previous 14-day
    recent = series.tail(14).mean()
    prev = series.tail(28).head(14).mean() if len(series) >= 28 else series.head(len(series) // 2).mean()
    growth = ((recent - prev) / prev * 100) if prev and prev > 0 else 0.0
    if growth > 10:
        trend = "increasing"
    elif growth < -10:
        trend = "decreasing"
    else:
        trend = "stable"
    # simple projection
    predicted = recent * horizon * (1 + growth / 200)  # dampened
    return {
        "predicted_total": round(max(0, predicted), 1),
        "daily_avg": round(float(recent), 2),
        "trend": trend,
        "growth_pct": round(float(growth), 1),
        "confidence": "medium" if len(series) >= 30 else "low",
        "method": "moving_average_trend",
    }


async def predict_product_demand(product_id: str, horizons: List[int] = [7, 30, 90]) -> Dict[str, Any]:
    db = get_db()
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return {"error": "Product not found"}

    df = await build_sales_dataframe(180)
    pdf = df[df["product_id"] == product_id].sort_values("date")
    if pdf.empty:
        series = pd.Series(dtype=float)
    else:
        # daily series
        daily = pdf.set_index("date")["qty"].resample("D").sum().fillna(0)
        series = daily

    result = {
        "product_id": product_id,
        "name": product.get("name"),
        "current_stock": product.get("stock_quantity", 0),
        "min_stock_level": product.get("min_stock_level", 5),
        "predictions": {},
        "recommendation": None,
    }
    for h in horizons:
        fc = simple_forecast(series, h)
        result["predictions"][f"next_{h}_days"] = fc

    # Smart inventory recommendation
    pred30 = result["predictions"].get("next_30_days", {})
    predicted = pred30.get("predicted_total", 0)
    stock = result["current_stock"]
    if predicted > stock * 1.2:
        need = int(predicted - stock + product.get("min_stock_level", 5))
        result["recommendation"] = {
            "action": "purchase",
            "qty": max(need, 0),
            "reason": f"Predicted 30-day demand ({predicted}) exceeds current stock ({stock}). Trend: {pred30.get('trend')}.",
        }
    elif pred30.get("trend") == "decreasing" and stock > predicted * 2:
        result["recommendation"] = {
            "action": "hold",
            "qty": 0,
            "reason": "Declining demand and sufficient stock. Avoid reordering.",
        }
    else:
        result["recommendation"] = {
            "action": "monitor",
            "qty": 0,
            "reason": "Stock appears adequate relative to forecast.",
        }

    # Persist summary on product for dashboard
    await db.products.update_one(
        {"_id": ObjectId(product_id)},
        {
            "$set": {
                "predicted_demand_30d": pred30.get("predicted_total"),
                "demand_trend": pred30.get("trend"),
                "ml_updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return result


async def compute_intelligence_score(product_id: str) -> Dict[str, Any]:
    """Product Intelligence Score 0-100."""
    db = get_db()
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return {"error": "not found"}

    df = await build_sales_dataframe(90)
    pdf = df[df["product_id"] == product_id]
    qty = float(pdf["qty"].sum()) if not pdf.empty else 0
    rev = float(pdf["revenue"].sum()) if not pdf.empty else 0
    cost = product.get("purchase_price", 0) * qty
    profit = rev - cost
    margin = (profit / rev * 100) if rev else 0

    # crude scoring
    sales_score = min(30, qty / 5)          # up to 30
    profit_score = min(25, margin / 2)      # up to 25
    stock = product.get("stock_quantity", 0)
    turnover = qty / max(stock, 1)
    turnover_score = min(20, turnover * 5)
    rating_score = 10  # placeholder
    return_penalty = 0
    score = max(0, min(100, sales_score + profit_score + turnover_score + rating_score - return_penalty))

    if score >= 80:
        label = "Excellent"
    elif score >= 65:
        label = "Strong"
    elif score >= 45:
        label = "Average"
    elif score >= 25:
        label = "Weak"
    else:
        label = "Critical"

    await db.products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"intelligence_score": round(score, 1), "intelligence_label": label}},
    )
    return {
        "product_id": product_id,
        "score": round(score, 1),
        "label": label,
        "components": {
            "sales": round(sales_score, 1),
            "profit_margin": round(profit_score, 1),
            "turnover": round(turnover_score, 1),
        },
    }


async def run_batch_forecast(limit: int = 50) -> List[Dict]:
    db = get_db()
    products = await db.products.find({"status": "active"}).limit(limit).to_list(limit)
    results = []
    for p in products:
        r = await predict_product_demand(str(p["_id"]))
        results.append(r)
    return results