from fastapi import FastAPI, Query
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.cluster import KMeans
from datetime import datetime, timedelta
from functools import wraps

app = FastAPI()

# ========== CORS Configuration ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = create_engine('postgresql://user:password@db:5432/stockdb')

# ========== CACHING SYSTEM ==========
cache_storage = {}

def cache_with_ttl(ttl_seconds: int):
    """
    Decorator để cache kết quả API với thời gian sống (TTL)
    - ttl_seconds: thời gian cache tính bằng giây
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Tạo cache key từ tên hàm và params
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Kiểm tra cache
            if cache_key in cache_storage:
                cached_data, cached_time = cache_storage[cache_key]
                
                # Kiểm tra còn hiệu lực không
                if datetime.now() - cached_time < timedelta(seconds=ttl_seconds):
                    print(f"✅ Cache hit: {func.__name__} (TTL: {ttl_seconds}s)")
                    return cached_data
                else:
                    print(f"⏰ Cache expired: {func.__name__}")
            
            # Gọi hàm thực tế nếu không có cache hoặc hết hạn
            print(f"🔄 Cache miss: {func.__name__} - fetching fresh data")
            result = func(*args, **kwargs)
            
            # Lưu vào cache
            cache_storage[cache_key] = (result, datetime.now())
            return result
        
        return wrapper
    return decorator

# ========== API ENDPOINTS ==========

# ---------- Full Database (5 phút) ----------
@app.get("/api/database")
@cache_with_ttl(300)  # 5 phút = 300 giây
def get_database():
    try:
        df = pd.read_sql("SELECT * FROM raw_stock_prices ORDER BY time ASC", db)
        if df.empty:
            return {"data": [], "msg": "Database is empty"}
        return {"data": df.replace({np.nan: None}).to_dict(orient="records")}
    except Exception as e:
        return {"data": [], "msg": str(e)}

# ---------- Distribution (5 phút) ----------
@app.get("/api/distribution")
@cache_with_ttl(300)  # 5 phút
def get_distribution(symbols: Optional[str] = Query(None, description="Comma-separated symbols"),
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None):
    tickers = [s.strip().upper() for s in symbols.split(",")] if symbols else ["HPG"]
    try:
        query = "SELECT * FROM raw_stock_prices WHERE ticker IN ({})".format(
            ",".join(["'{}'".format(t) for t in tickers])
        )
        if start_date:
            query += " AND time >= '{}'".format(start_date)
        if end_date:
            query += " AND time <= '{}'".format(end_date)
        df = pd.read_sql(query, db)
        if df.empty:
            return {"data": [], "msg": "No data"}
        return {"data": df[['time','ticker','close','volume']].replace({np.nan: None}).to_dict(orient="records")}
    except Exception as e:
        return {"data": [], "msg": str(e)}

# ---------- Prediction (5 phút) ----------
@app.get("/api/prediction")
@cache_with_ttl(300)  # 5 phút
def get_prediction(symbols: Optional[str] = Query(None, description="Comma-separated symbols")):
    tickers = [s.strip().upper() for s in symbols.split(",")] if symbols else ["HPG"]
    results = []
    try:
        for t in tickers:
            df = pd.read_sql("SELECT * FROM raw_stock_prices WHERE ticker='{}' ORDER BY time ASC".format(t), db)
            if df.empty or len(df) < 30:
                continue
            df['day_id'] = np.arange(len(df))
            X = df[['day_id']].astype(float)
            y = df['close']
            y_class = (df['close'].shift(-1) > df['close']).astype(int).fillna(0)

            # Linear Regression dự đoán giá
            reg = LinearRegression().fit(X, y)
            next_day = pd.DataFrame([[len(df)+1]], columns=['day_id']).astype(float)
            pred_price = int(round(reg.predict(next_day)[0], 0))

            # Đồng bộ trend dựa trên giá dự đoán
            today_price = int(round(df['close'].iloc[-1], 0))
            pred_trend = "Tăng" if pred_price > today_price else "Giảm"

            results.append({
                "ticker": t,
                "today_price": today_price,
                "next_price": pred_price,
                "trend": pred_trend
            })
        return {"data": results}
    except Exception as e:
        return {"data": [], "msg": str(e)}

# ---------- Trend (5 phút) ----------
@app.get("/api/trend")
@cache_with_ttl(300)  # 5 phút
def get_trend(symbols: Optional[str] = Query(None, description="Comma-separated symbols")):
    tickers = [s.strip().upper() for s in symbols.split(",")] if symbols else ["HPG"]
    results = []
    try:
        for t in tickers:
            df = pd.read_sql(f"SELECT * FROM raw_stock_prices WHERE ticker='{t}' ORDER BY time ASC", db)
            if df.empty:
                continue
            df.set_index('time', inplace=True)
            monthly = df['close'].resample('M').mean().reset_index()
            monthly['ticker'] = t
            results.append(monthly)
        if results:
            df_out = pd.concat(results).reset_index(drop=True)
            return {"data": df_out.to_dict(orient="records")}
        return {"data": []}
    except Exception as e:
        return {"data": [], "msg": str(e)}

# ---------- Seasonal (5 phút) ----------
@app.get("/api/seasonal")
@cache_with_ttl(300)  # 5 phút
def get_seasonal(symbols: Optional[str] = Query(None, description="Comma-separated symbols")):
    tickers = [s.strip().upper() for s in symbols.split(",")] if symbols else ["HPG"]
    results = []
    try:
        for t in tickers:
            df = pd.read_sql(f"SELECT * FROM raw_stock_prices WHERE ticker='{t}' ORDER BY time ASC", db)
            if df.empty:
                continue
            df.set_index('time', inplace=True)
            monthly_avg = df['close'].resample('M').mean().reset_index()
            monthly_avg['ticker'] = t
            results.append(monthly_avg)
        if results:
            df_out = pd.concat(results).reset_index(drop=True)
            return {"data": df_out.to_dict(orient="records")}
        return {"data": []}
    except Exception as e:
        return {"data": [], "msg": str(e)}

# ---------- Clustering (1 ngày) ----------
@app.get("/api/clustering")
@cache_with_ttl(86400)  # 1 ngày = 86400 giây
def get_clustering():
    try:
        # Lấy tất cả ticker trong DB
        tickers_df = pd.read_sql("SELECT DISTINCT ticker FROM raw_stock_prices", db)
        tickers = tickers_df["ticker"].tolist()

        if not tickers:
            return {"data": [], "msg": "No tickers found"}

        query = "SELECT * FROM raw_stock_prices WHERE ticker IN ({})".format(
            ",".join([f"'{t}'" for t in tickers])
        )
        df = pd.read_sql(query, db)

        if df.empty:
            return {"data": [], "msg": "No price data"}

        pivot = df.pivot_table(index='time', columns='ticker', values='close')
        rets = pivot.pct_change().mean() * 252
        vola = pivot.pct_change().std() * (252**0.5)

        data = pd.DataFrame({
            "returns": rets,
            "volatility": vola,
            "ticker": rets.index
        }).fillna(0)

        if len(data) >= 3:
            kmeans = KMeans(n_clusters=3, n_init=10, random_state=42).fit(data[["returns", "volatility"]])
            data["cluster"] = kmeans.labels_
        else:
            data["cluster"] = 0

        return {"data": data.reset_index(drop=True).to_dict(orient="records")}

    except Exception as e:
        return {"data": [], "msg": str(e)}

# ---------- Correlation (5 phút) ----------
@app.get("/api/correlation")
@cache_with_ttl(300)  # 5 phút
def get_correlation(
    symbols: Optional[str] = Query(None, description="Comma-separated tickers"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Trả về correlation matrix của các cổ phiếu theo giá đóng cửa.
    Query params:
    - symbols: "HPG,VCB,ACB" (mặc định lấy tất cả)
    - start_date: "YYYY-MM-DD"
    - end_date: "YYYY-MM-DD"
    """
    try:
        # Lấy tất cả tickers nếu không truyền symbols
        if symbols:
            tickers = [s.strip().upper() for s in symbols.split(",")]
        else:
            tickers_df = pd.read_sql("SELECT DISTINCT ticker FROM raw_stock_prices", db)
            tickers = tickers_df["ticker"].tolist()

        if not tickers:
            return {"data": {}, "msg": "No tickers found"}

        # Build SQL query
        query = "SELECT time, ticker, close FROM raw_stock_prices WHERE ticker IN ({})".format(
            ",".join([f"'{t}'" for t in tickers])
        )
        if start_date:
            query += f" AND time >= '{start_date}'"
        if end_date:
            query += f" AND time <= '{end_date}'"

        df = pd.read_sql(query, db)

        if df.empty:
            return {"data": {}, "msg": "No data found"}

        # Pivot table: index=time, columns=ticker, values=close
        pivot = df.pivot_table(index='time', columns='ticker', values='close')

        # Tính correlation
        corr_matrix = pivot.corr()

        # Chuyển sang dict để JSON trả về
        return {"data": corr_matrix.fillna(0).to_dict()}
    except Exception as e:
        return {"data": {}, "msg": str(e)}

# ========== CACHE MANAGEMENT ENDPOINTS ==========

@app.get("/api/cache/clear")
def clear_cache():
    """Xóa toàn bộ cache"""
    cache_storage.clear()
    return {"msg": "Cache cleared successfully", "timestamp": datetime.now().isoformat()}

@app.get("/api/cache/status")
def cache_status():
    """Kiểm tra trạng thái cache"""
    status = []
    for key, (data, cached_time) in cache_storage.items():
        status.append({
            "key": key,
            "cached_at": cached_time.isoformat(),
            "age_seconds": (datetime.now() - cached_time).total_seconds()
        })
    return {
        "total_cached_items": len(cache_storage),
        "cache_details": status
    }