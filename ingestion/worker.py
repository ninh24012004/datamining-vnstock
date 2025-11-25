import time
from vnstock import stock_historical_data
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime, timedelta

SYMBOLS = [
    'ACB', 'BCM', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
    'MBB', 'MSN', 'MWG', 'PLX', 'POW', 'SAB', 'SHB', 'SSB', 'SSI', 'STB',
    'TCB', 'TPB', 'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB', 'VRE'
]
DAYS_BACK = 365 
DB_URI = 'postgresql://user:password@db:5432/stockdb'

def fetch_raw_data():
    print(f"\n--- INGESTION START: {datetime.now()} ---")
    try:
        db_engine = create_engine(DB_URI)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=DAYS_BACK)).strftime('%Y-%m-%d')

        all_data = []
        count = 0
        for sym in SYMBOLS:
            try:
                df = stock_historical_data(symbol=sym, start_date=start_date, end_date=end_date, resolution='1D', type='stock')
                if df is not None and not df.empty:
                    df['ticker'] = sym
                    all_data.append(df)
                    count += 1
                time.sleep(0.1)
            except:
                print(f"Error fetching {sym}")

        if all_data:
            final_df = pd.concat(all_data)
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
    print("Waiting for Database...")
    time.sleep(10)
    fetch_raw_data()
    while True:
        print("Sleeping 5 minutes...")
        time.sleep(300)