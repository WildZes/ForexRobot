import pandas as pd
import matplotlib.dates as mdates
import numpy as np
import os.path as op


def time_to_num(time):
    return mdates.datestr2num(time)


def create_y_x_A_m_c(quotes):
    y = np.array(quotes[['Open', 'High', 'Low', 'Close']]).ravel()
    x = np.array(quotes.index).ravel()
    x = np.array([(lambda d: mdates.date2num(d))(d) for d in x for _ in (0,1,2,3)])
    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y, rcond=None)[0]
    return y, x, A, m, c


#Define trend direction
def trend_dir(quotes):
    _, _, _, m, _ = create_y_x_A_m_c(quotes)
    if m < 0:
        _dir = -1
    elif m > 0:
        _dir = 1
    else:
        _dir = 0 #have to organize check for sideway trend somehow (28.02.2021 update: orginized via get_ength and calculating median for it)
    return _dir


#Dataframe creation
def get_df():
    cur_path = r'C:\Users\mrP\AppData\Roaming\MetaQuotes\Terminal\C9EACFC244DF3C49B263EE60244932A4\MQL4\Files\data.csv'
    if op.isfile(cur_path):
        col_names=['DateTime','Open','High','Low','Close','Tick_Vol']
        df = pd.read_csv (cur_path, names=col_names)
        df['DateTime']=pd.to_datetime(df.pop('DateTime'))
        my_df = df.set_index('DateTime')
        return my_df
    raise NameError('get_df is broken')


#Function that helps to define change of trand direction (RSI < 70 and RSI > 30: OK)
def RSI(series, period):
    delta = series.diff().dropna()
    u = delta * 0
    d = u.copy()
    u[delta > 0] = delta[delta > 0]
    d[delta < 0] = -delta[delta < 0]
    u[u.index[period-1]] = np.mean( u[:period] ) #first value is sum of avg gains
    u = u.drop(u.index[:(period-1)])
    d[d.index[period-1]] = np.mean( d[:period] ) #first value is sum of avg losses
    d = d.drop(d.index[:(period-1)])
    rs = u.ewm(com=period-1, adjust=False).mean() / d.ewm(com=period-1, adjust=False).mean()
    return 100 - 100 / (1 + rs)

#Function to estimate treshold strength and volume
def get_m_v(strengthList, volumeList, all_df):
    _, _, _, m, _ = create_y_x_A_m_c(all_df)
    strengthList.append(abs(m))
    tmp = all_df['Tick_Vol'].values
    volumeList += tmp.tolist()
    return np.mean(strengthList), np.mean(volumeList), strengthList, volumeList


#Function to check if price is in right place relative trend line
def check_price(price, time, m, c):
    trend_dot = time * m + c
    if (price>trend_dot)&(m<0):
        return True
    if (price<trend_dot)&(m>0):
        return True
    return False


#Function that checks, if price crossed trend line less than 5 times
def traversal_fiveless(quotes):
    y, x, A, m, c = create_y_x_A_m_c(quotes)
    x_scale = pd.DataFrame(x).drop_duplicates()
    primary = check_price(quotes.Close[0], x_scale[0].iloc[0], m, c)
    traversal = 0
    quotes['date_to_num'] = x_scale[0].values
    for t in x_scale[0]:        
        t_prim = check_price(quotes.Close.loc[quotes['date_to_num'] == t].values[0], t, m, c)
        if primary == t_prim or primary:
            continue
        primary = t_prim
        traversal += 1
        if traversal > 4:
            return False
    return True
