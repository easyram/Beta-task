import requests
import pandas as pd
import json
import time
import matplotlib.pyplot as plt

# top US companies by market cap taken from http://www.iweblists.com/us/commerce/MarketCapitalization.html
tickers = ['KO','CMCSA','CRM','WMT','TMO','GS',
           'MSFT','ACN','OXY','ADBE','MMM','AAPL','ABBV',
           'SLB','AXP','IBM','USB','BMY','CSCO',
           'BAC','PM','COP','CHTR','PEP','HPQ','JPM',
           'UPS','PG','BRK.B','T','HD','INTC','ABT',
           'ORCL','BA','UNH','QCOM','V','UNP','LLY',
           'GOOG','AMGN','NKE','COST','NEE','GE','MDT',
           'CVX','MO','F','C','DIS','BIIB', 'AMZN',
           'NVDA','PFE','WBA','VZ','XOM','MRK','MA',
           'NFLX','WFC','GILD','MCD','CVS',
           'FB','JNJ','PYPL']

# download daily market cap from https://stockrow.com to pandas dataframe
s = requests.Session()
payload = {"indicators":["24384118-e242-4b95-a226-34e3fb7d2f14"],"tickers":[],"start_date":"2010-03-01T00:00:00.000+03:00"}

df = pd.DataFrame()
for ticker in tickers:
    payload['tickers'] = [ticker]
    while True:
        try:
            data = s.post("https://stockrow.com/api/fundamentals.json",data = payload)
            data = json.loads(data.text)['series'][0]['data']
            break
        except Exception as e:
            time.sleep(5)
        
    df_column = pd.DataFrame(data).set_index(0)
    df_column.columns = [ticker]
    if not len(df):
        df = df_column
    else:
        df = pd.concat([df,df_column],axis=1)
        
df.index = pd.to_datetime(df.index/1000,unit='s')

# pick up top 10 companies by market cap every 20 days and assign weights based by 20 days returns
df_returns = df.pct_change(periods=20)
weights_df = pd.DataFrame(index=df.index,columns=df.columns)

weights = [0.1 for i in range(0,10)]
j = -1
for i,row in df.iterrows():
    j+=1
    if j%20 == 0:
        top_cap = row.sort_values(ascending=False).dropna()
        top_cap_list = top_cap.index[:10].to_list()

        ret = df_returns[top_cap_list].loc[i]
        
        if ret.isnull().values.any():
            weights_df.loc[i][top_cap_list] = 1/10
        else:
            ret = ret.sort_values(ascending=True)
            r_min = ret.min()
            r_max = ret.max()
            weights = [((x-r_min)/(r_max-r_min+0.001))**1 for x in ret.values]
            s_weights = sum(weights)
            
            weights = [x/s_weights for x in weights]

    weights_df.loc[i][ret.index.to_list()] = weights
    
# calculate returns of the portfolio
df_daily_returns = df.pct_change()
P_returns = df_daily_returns.shift(-1)*weights_df
P_returns = P_returns.sum(axis=1)

# plot the portfolio returns
P_returns.cumsum().plot(figsize=(20,10))
plt.show()
