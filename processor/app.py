# processor.py
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
import time
from datetime import datetime, timedelta
from sqlalchemy.exc import OperationalError

DB_URI = 'postgresql://user:password@db:5432/stockdb'
db = create_engine(DB_URI)

def wait_for_db(engine, timeout=60):
    """Chờ DB sẵn sàng trước khi chạy"""
    start = time.time()
    while True:
        try:
            conn = engine.connect()
            conn.close()
            print("Database is ready!")
            return
        except OperationalError:
            if time.time() - start > timeout:
                raise TimeoutError("Database not ready after waiting.")
            print("Waiting for database...")
            time.sleep(2)

# ---------- Lấy full database ----------
def get_full_database():
    df = pd.read_sql("SELECT * FROM raw_stock_prices ORDER BY time ASC", db)
    return df.replace({np.nan: None})

# ---------- Distribution ----------
def compute_distribution(symbols=None, start_date=None, end_date=None):
    if symbols:
        tickers = [s.strip().upper() for s in symbols.split(",")]
    else:
        tickers_df = pd.read_sql("SELECT DISTINCT ticker FROM raw_stock_prices", db)
        tickers = tickers_df["ticker"].tolist()
    
    query = "SELECT * FROM raw_stock_prices WHERE ticker IN ({})".format(
        ",".join([f"'{t}'" for t in tickers])
    )
    if start_date:
        query += f" AND time >= '{start_date}'"
    if end_date:
        query += f" AND time <= '{end_date}'"
    df = pd.read_sql(query, db)
    df_out = df[['time','ticker','close','volume']].replace({np.nan: None})

    if not df_out.empty:
        df_out.to_sql('distribution_table', db, if_exists='replace', index=False)
    return df_out

# ---------- Prediction ----------
def compute_prediction():
    tickers_df = pd.read_sql("SELECT DISTINCT ticker FROM raw_stock_prices", db)
    tickers = tickers_df["ticker"].tolist()
    results = []

    for t in tickers:
        df = pd.read_sql(f"SELECT * FROM raw_stock_prices WHERE ticker='{t}' ORDER BY time ASC", db)
        if df.empty or len(df) < 30:
            continue
        df['day_id'] = np.arange(len(df))
        X = df[['day_id']].astype(float)
        y = df['close']

        reg = LinearRegression().fit(X, y)
        next_day = pd.DataFrame([[len(df)+1]], columns=['day_id']).astype(float)
        pred_price = int(round(reg.predict(next_day)[0], 0))
        today_price = int(round(df['close'].iloc[-1], 0))
        pred_trend = "Tăng" if pred_price > today_price else "Giảm"

        results.append({
            "ticker": t,
            "today_price": today_price,
            "next_price": pred_price,
            "trend": pred_trend
        })

    if results:
        df_pred = pd.DataFrame(results)
        df_pred.to_sql('prediction_table', db, if_exists='replace', index=False)
        print(f"[Prediction] Updated {len(df_pred)} rows")
    return results

# ---------- Trend ----------
def compute_trend():
    tickers_df = pd.read_sql("SELECT DISTINCT ticker FROM raw_stock_prices", db)
    tickers = tickers_df["ticker"].tolist()
    results = []

    for t in tickers:
        df = pd.read_sql(f"SELECT * FROM raw_stock_prices WHERE ticker='{t}' ORDER BY time ASC", db)
        if df.empty:
            continue
        df.set_index('time', inplace=True)
        monthly = df['close'].resample('M').mean().reset_index()
        monthly['ticker'] = t
        results.append(monthly)

    if results:
        df_trend = pd.concat(results).reset_index(drop=True)
        df_trend.to_sql('trend_table', db, if_exists='replace', index=False)
        print(f"[Trend] Updated trend_table with {len(df_trend)} rows")
        return df_trend
    return pd.DataFrame()

# ---------- Seasonal ----------
def compute_seasonal():
    df_seasonal = compute_trend()
    if not df_seasonal.empty:
        df_seasonal.to_sql('seasonal_table', db, if_exists='replace', index=False)
        print(f"[Seasonal] Updated seasonal_table with {len(df_seasonal)} rows")
    return df_seasonal

# ---------- Clustering ----------
def compute_clustering():
    tickers_df = pd.read_sql("SELECT DISTINCT ticker FROM raw_stock_prices", db)
    tickers = tickers_df["ticker"].tolist()
    if not tickers:
        return pd.DataFrame()

    query = "SELECT * FROM raw_stock_prices WHERE ticker IN ({})".format(
        ",".join([f"'{t}'" for t in tickers])
    )
    df = pd.read_sql(query, db)
    if df.empty:
        return pd.DataFrame()

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

    data.to_sql('clustering_table', db, if_exists='replace', index=False)
    print(f"[Clustering] Updated clustering_table with {len(data)} rows")
    return data.reset_index(drop=True)

# ---------- Correlation ----------
def compute_correlation():
    try:
        df = pd.read_sql("SELECT time, ticker, close FROM raw_stock_prices", db)
        if df.empty:
            print("[Correlation] No data found")
            return {}

        pivot = df.pivot_table(index='time', columns='ticker', values='close')
        corr_matrix = pivot.corr().fillna(0)
        corr_matrix.to_sql('correlation_table', db, if_exists='replace', index_label='ticker')
        print(f"[Correlation] Updated correlation_table with {len(corr_matrix)} rows")
        return corr_matrix.to_dict(orient='index')

    except Exception as e:
        print(f"[Correlation] Error: {e}")
        return {}

# ---------- Main loop ----------
def main_loop(interval=300):
    wait_for_db(db)
    print("Processor started, running in daemon mode...")

    last_clustering = datetime.min  # lần clustering cuối cùng

    while True:
        try:
            print("Running regular compute tasks...")
            compute_distribution()
            compute_prediction()
            compute_trend()
            compute_seasonal()
            compute_correlation()
            print("Regular tasks done.")

            # Clustering chạy 1 ngày 1 lần
            now = datetime.now()
            if now - last_clustering >= timedelta(days=1):
                print("Running daily clustering task...")
                compute_clustering()
                last_clustering = now
                print("Clustering done.")

            print(f"Sleeping {interval}s...\n")
            time.sleep(interval)

        except Exception as e:
            print(f"Error occurred: {e}, retrying in {interval}s")
            time.sleep(interval)

if __name__ == "__main__":
    main_loop(interval=300)
