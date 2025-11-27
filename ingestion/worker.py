import time
from vnstock import stock_historical_data
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime

SYMBOLS = [
    'ACB', 'BCM', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
    'MBB', 'MSN', 'MWG', 'PLX', 'POW', 'SAB', 'SHB', 'SSB', 'SSI', 'STB',
    'TCB', 'TPB', 'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB', 'VRE'
]

DB_URI = 'postgresql://user:password@db:5432/stockdb'

def wait_for_db(engine, timeout=60):
    """Chờ DB sẵn sàng trước khi chạy"""
    start = time.time()
    while True:
        try:
            conn = engine.connect()
            conn.close()
            print("Database is ready!")
            return
        except Exception:
            if time.time() - start > timeout:
                raise TimeoutError("Database not ready after waiting.")
            print("Waiting for database...")
            time.sleep(2)

def fetch_raw_data():
    print(f"\n--- INGESTION START: {datetime.now()} ---")
    try:
        db_engine = create_engine(DB_URI)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = '2020-01-01'  # Lấy từ đầu 2020

        all_data = []
        count = 0
        for sym in SYMBOLS:
            try:
                print(f"Fetching {sym}...")
                df = stock_historical_data(
                    symbol=sym,
                    start_date=start_date,
                    end_date=end_date,
                    resolution='1D',
                    type='stock'
                )
                if df is not None and not df.empty:
                    df['ticker'] = sym
                    all_data.append(df)
                    count += 1
                else:
                    print(f"No data for {sym}")
                time.sleep(0.1)  # tránh bị block API
            except Exception as e:
                print(f"Error fetching {sym}: {e}")

        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            final_df.columns = final_df.columns.str.lower()
            if 'time' in final_df.columns:
                final_df['time'] = pd.to_datetime(final_df['time'])

            final_df.to_sql('raw_stock_prices', db_engine, if_exists='replace', index=False)
            print(f">>> SUCCESS: Saved {len(final_df)} rows of {count} symbols.")
        else:
            print(">>> WARNING: No data fetched.")

    except Exception as e:
        print(f"Ingestion Error: {e}")

if __name__ == "__main__":
    db_engine = create_engine(DB_URI)
    wait_for_db(db_engine)
    while True:
        fetch_raw_data()
        print("Sleeping 5 minutes...")
        time.sleep(300)
