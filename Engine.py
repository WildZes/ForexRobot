from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector
from time import sleep
from io import StringIO
import os
import sys

#Define trend direction
def trend_dir(quotes):
    import pandas as pd
    import matplotlib.dates as mdates
    import numpy as np
    y = np.array(quotes[['Open', 'High', 'Low', 'Close']]).ravel()
    x = np.array(quotes.index).ravel()
    x = np.array([(lambda d: mdates.date2num(d))(d) for d in x for _ in (0,1,2,3)])
    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y, rcond=None)[0]
    if m < 0:
        _dir = -1
    elif m > 0:
        _dir = 1
    else:
        _dir = 0 #have to organize check for sideway trend somehow (28.02.2021 update: orginized via get_ength and calculating median for it)
    return _dir


#Dataframe creation
def get_df():
    import pandas as pd
    cur_path = r'C:\Users\mrP\AppData\Roaming\MetaQuotes\Terminal\C9EACFC244DF3C49B263EE60244932A4\MQL4\Files\data.csv'
    if os.path.isfile(cur_path):
        col_names=['DateTime','Open','High','Low','Close','Tick_Vol']
        df = pd.read_csv (cur_path, names=col_names)
        df['DateTime']=pd.to_datetime(df.pop('DateTime'))
        my_df = df.set_index('DateTime')
        return my_df


#Function to get oped as int
def f_get(command):
    sys.stdout = result
    command()
    sleep(0.2)
    out = result.getvalue()
    sys.stdout = origin_stdout
    return out


#On start (no open orders)
def run(oped):
    if 'Error' in oped:
        raise NameError(oped)
    if 'OPEN_TRADES' in oped:
        return re_run()
    try:
        openCurList = f_get(_zmq._DWX_MTX_GET_ALL_OPEN_TRADES_)
        while int(oped) < 4:
            arrSymbol = [ok for ok in currencyList
                         if ok in openCurList]
            for cur in currencyList:
                if cur in arrSymbol:
                    continue
                _zmq._DWX_MTX_SEND_MARKETDATA_REQUEST_(_symbol=cur, _timeframe=240,
                                                       _start='2020.1.1', _end='2020.1.2')
                sleep(0.3)
                df_H4 = get_df()
                _zmq._DWX_MTX_SEND_MARKETDATA_REQUEST_(_symbol=cur, _timeframe=1440,
                                                       _start='2020.1.1', _end='2020.1.2')
                sleep(0.3)
                df_D1 = get_df()
                if trend_dir(df_H4) != trend_dir(df_D1):
                    continue              
        oped = f_get(_zmq._SPI_ZMQ_GET_OPED_())
        return re_run()
    except Exception as e:
        raise NameError(e.args)

#To wait changes
def re_run():
    sleep(1) #1440 for 4 hours
    return run(f_get(_zmq._SPI_ZMQ_GET_OPED_))


currencyList = ['AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADCHF', 'CADJPY', 'CHFJPY', 'EURAUD', 'EURCAD',
                'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD', 'GBPCHF', 'GBPJPY', 'GBPUSD', 'NZDJPY', 'NZDUSD',
                'USDCAD', 'USDCHF', 'USDJPY', 'GBPAUD', 'GBPNZD', 'GBPCAD', 'NZDCHF', 'NZDCAD']
timeframeList = ['1', '5', '15', '30', '60', '240', '1440', '10080']
origin_stdout = sys.stdout
result = StringIO()
_zmq = DWX_ZeroMQ_Connector()

if __name__ == "__main__":
    try:
        run(f_get(_zmq._SPI_ZMQ_GET_OPED_))
    except KeyboardInterrupt:
        sys.stdout = origin_stdout
    except NameError:
        raise
    finally:
        sys.stdout = origin_stdout