from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from sqlalchemy import create_engine
from typing import Optional  # <-- Thêm

DB_URI = 'postgresql://user:password@db:5432/stockdb'
db = create_engine(DB_URI)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_table(table_name):
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", db)
        return df
    except Exception:
        return pd.DataFrame()


def filter_symbols(df: pd.DataFrame, symbols: Optional[str]):
    """Lọc theo danh sách symbols, tách bằng dấu ','"""
    if df.empty:
        return df
    if symbols:
        tickers = [s.strip().upper() for s in symbols.split(",")]
        df = df[df["ticker"].isin(tickers)]
    return df


@app.get("/api/database")
def api_database():
    df = read_table('raw_stock_prices')
    return {"data": df.to_dict(orient="records")} if not df.empty else {"data": []}


@app.get("/api/distribution")
def api_distribution(symbols: Optional[str] = Query(None)):
    df = read_table('distribution_table')
    df = filter_symbols(df, symbols)
    return {"data": df.to_dict(orient="records")}


@app.get("/api/prediction")
def api_prediction(symbols: Optional[str] = Query(None)):
    df = read_table('prediction_table')
    df = filter_symbols(df, symbols)
    return {"data": df.to_dict(orient="records")}


@app.get("/api/trend")
def api_trend(symbols: Optional[str] = Query(None)):
    df = read_table('trend_table')
    df = filter_symbols(df, symbols)
    return {"data": df.to_dict(orient="records")}


@app.get("/api/seasonal")
def api_seasonal(symbols: Optional[str] = Query(None)):
    df = read_table('seasonal_table')
    df = filter_symbols(df, symbols)
    return {"data": df.to_dict(orient="records")}


@app.get("/api/clustering")
def api_clustering():
    df = read_table('clustering_table')
    return {"data": df.to_dict(orient="records")} if not df.empty else {"data": []}


@app.get("/api/correlation")
def api_correlation():
    df = read_table('correlation_table')
    return {"data": df.to_dict()} if not df.empty else {"data": {}}
