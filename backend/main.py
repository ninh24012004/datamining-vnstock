from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
import pandas as pd
import numpy as np

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

db = create_engine('postgresql://user:password@db:5432/stockdb')

def get_safe(table, ticker=None):
    try:
        query = f"SELECT * FROM {table}"
        if ticker: query += f" WHERE ticker = '{ticker}'"
        df = pd.read_sql(query, db)
        if df.empty: return []
        return df.replace({np.nan: None}).to_dict(orient="records")
    except: return []

@app.get("/api/trend")
def get_trend(symbol: str = "HPG"): return get_safe("chart_trend", symbol)

@app.get("/api/distribution")
def get_dist(symbol: str = "HPG"): return get_safe("chart_distribution", symbol)

@app.get("/api/prediction")
def get_pred(symbol: str = "HPG"): return get_safe("chart_prediction", symbol)

@app.get("/api/correlation")
def get_corr(): return get_safe("chart_correlation")

@app.get("/api/clustering")
def get_clust(): return get_safe("chart_clustering")