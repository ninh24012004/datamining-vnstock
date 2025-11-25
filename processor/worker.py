import time
import pandas as pd
import numpy as np
import warnings
from sklearn.exceptions import DataConversionWarning
warnings.filterwarnings(action='ignore', category=FutureWarning)
warnings.filterwarnings(action='ignore', category=UserWarning)
warnings.filterwarnings(action='ignore', category=DataConversionWarning)

from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.cluster import KMeans

DB_URI = 'postgresql://user:password@db:5432/stockdb'

class BaseChartProcessor:
    def __init__(self, db_uri):
        self.engine = create_engine(db_uri)
    
    def load_raw_data(self):
        try:
            df = pd.read_sql("SELECT * FROM raw_stock_prices", self.engine)
            if not df.empty:
                df['time'] = pd.to_datetime(df['time'])
                df = df.sort_values(by='time')
            return df
        except: return pd.DataFrame()

    def save_to_db(self, df, table_name):
        if df is not None and not df.empty:
            df.to_sql(table_name, self.engine, if_exists='replace', index=False)
            print(f"   [OK] Saved: {table_name}")

class TrendProcessor(BaseChartProcessor):
    def process(self, df):
        tickers = df['ticker'].unique()
        results = []
        for sym in tickers:
            d_sym = df[df['ticker'] == sym].copy().set_index('time')
            if d_sym.empty: continue
            
            d = d_sym['close'].reset_index()
            d['type'] = 'Daily'; d['ticker'] = sym
            
            w = d_sym['close'].resample('W').mean().reset_index()
            w['type'] = 'Weekly Trend'; w['ticker'] = sym
            
            m = d_sym['close'].resample('ME').mean().reset_index()
            m['type'] = 'Monthly Seasonal'; m['ticker'] = sym
            
            results.append(pd.concat([d, w, m]))
        
        if results: self.save_to_db(pd.concat(results), 'chart_trend')

class DistributionProcessor(BaseChartProcessor):
    def process(self, df):
        if df.empty: return
        self.save_to_db(df[['time', 'ticker', 'close', 'volume']], 'chart_distribution')

class CorrelationProcessor(BaseChartProcessor):
    def process(self, df):
        pivot = df.pivot_table(index='time', columns='ticker', values='close')
        if pivot.empty: return
        self.save_to_db(pivot.corr().reset_index(), 'chart_correlation')

class PredictionProcessor(BaseChartProcessor):
    def process(self, df):
        tickers = df['ticker'].unique()
        preds = []
        for sym in tickers:
            d_sym = df[df['ticker'] == sym].copy()
            if len(d_sym) < 30: continue
            
            d_sym['day_id'] = np.arange(len(d_sym))
            X = d_sym[['day_id']]
            y = d_sym['close']
            y_class = (d_sym['close'].shift(-1) > d_sym['close']).astype(int).fillna(0)
            
            try:
                reg = LinearRegression().fit(X, y)
                next_day = pd.DataFrame([[len(d_sym) + 1]], columns=['day_id'])
                pred_price = reg.predict(next_day)[0]
                
                clf = LogisticRegression().fit(X[:-1], y_class[:-1])
                pred_trend = clf.predict(next_day)[0]
                
                preds.append({'ticker': sym, 'next_price': pred_price, 'trend': 'Tăng' if pred_trend==1 else 'Giảm'})
            except: continue
            
        if preds: self.save_to_db(pd.DataFrame(preds), 'chart_prediction')

class ClusteringProcessor(BaseChartProcessor):
    def process(self, df):
        pivot = df.pivot_table(index='time', columns='ticker', values='close')
        if pivot.empty: return
        
        rets = pivot.pct_change().mean() * 252
        vola = pivot.pct_change().std() * (252**0.5)
        data = pd.DataFrame({'returns': rets, 'volatility': vola}).fillna(0)
        
        if len(data) >= 3:
            kmeans = KMeans(n_clusters=3, n_init=10).fit(data)
            data['cluster'] = kmeans.labels_
        else: data['cluster'] = 0
        
        data['ticker'] = data.index
        self.save_to_db(data, 'chart_clustering')

if __name__ == "__main__":
    print("--- PROCESSOR STARTED (CLEAN LOGS) ---")
    base = BaseChartProcessor(DB_URI)
    processors = [TrendProcessor(DB_URI), DistributionProcessor(DB_URI), CorrelationProcessor(DB_URI), PredictionProcessor(DB_URI), ClusteringProcessor(DB_URI)]
    while True:
        raw = base.load_raw_data()
        if not raw.empty:
            for p in processors:
                try: p.process(raw)
                except Exception as e: print(f"Err {p.__class__.__name__}: {e}")
        else: print("Waiting data...")
        print("Calculations done. Sleeping 5 mins..."); time.sleep(300)