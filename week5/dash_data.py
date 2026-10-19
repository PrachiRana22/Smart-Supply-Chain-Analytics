"""Data layer for the Smart Supply Chain dashboard (pandas only, so it can be tested without Plotly/Dash)."""

import glob
import numpy as np
import pandas as pd

USE = [
    "Order Id",
    "Order Item Id",
    "order date (DateOrders)",
    "Shipping Mode",
    "Market",
    "Order Region",
    "Customer Segment",
    "Category Name",
    "Delivery Status",
    "Late_delivery_risk",
    "Sales",
    "Order Profit Per Order",
    "Order Item Discount Rate",
    "Days for shipment (scheduled)",
    "Days for shipping (real)",
]


def load_data(path=None):
    path = path or glob.glob("*.csv*")[0]
    df = pd.read_csv(path, usecols=USE, encoding="utf-8")  # personal columns are never loaded
    df["order_date"] = pd.to_datetime(df["order date (DateOrders)"])
    df["month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    df["cancelled"] = df["Delivery Status"].eq("Shipping canceled")
    df["is_late"] = np.where(df["cancelled"], np.nan, df["Late_delivery_risk"].astype(float))
    df["discount_band"] = pd.cut(
        df["Order Item Discount Rate"],
        [-0.001, 0.05, 0.10, 0.15, 0.20, 0.25],
        labels=["0-5%", "5-10%", "10-15%", "15-20%", "20-25%"],
    )
    return df


def filter_data(df, markets=None, modes=None, start=None, end=None):
    m = pd.Series(True, index=df.index)
    if markets:
        m &= df["Market"].isin(markets)
    if modes:
        m &= df["Shipping Mode"].isin(modes)
    if start:
        m &= df["order_date"] >= pd.Timestamp(start)
    if end:
        m &= df["order_date"] <= pd.Timestamp(end)
    return df[m]


def kpis(d):
    sales, profit = d["Sales"].sum(), d["Order Profit Per Order"].sum()
    return {
        "sales": sales,
        "profit": profit,
        "margin": profit / sales if sales else np.nan,
        "orders": d["Order Id"].nunique(),
        "late_rate": d["is_late"].mean(),
        "cancelled": int(d["cancelled"].sum()),
    }


def monthly(d):
    return (
        d.groupby("month")
        .agg(
            orders=("Order Id", "nunique"), items=("Order Item Id", "count"), sales=("Sales", "sum")
        )
        .reset_index()
    )


def late_by_mode(d):
    x = d[~d["cancelled"]].groupby("Shipping Mode")["is_late"].agg(["mean", "count"]).reset_index()
    return x.rename(columns={"mean": "late_rate", "count": "items"}).sort_values("late_rate")


def margin_by_category(d, top=15):
    g = (
        d.groupby("Category Name")
        .agg(sales=("Sales", "sum"), profit=("Order Profit Per Order", "sum"))
        .reset_index()
    )
    g["margin"] = g["profit"] / g["sales"]
    return g.sort_values("sales", ascending=False).head(top)


def profit_by_discount(d):
    return d.groupby("discount_band", observed=True)["Order Profit Per Order"].mean().reset_index()
