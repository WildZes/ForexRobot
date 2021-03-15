from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector
from time import sleep
from io import StringIO
import sys
import MT4_calculations as MT4


#Function to get oped as int
def f_get(command):
    result = StringIO()
    sys.stdout = result
    command()
    sleep(0.5)
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
        while int(oped[0]) < 4:
            openCurList = f_get(_zmq._DWX_MTX_GET_ALL_OPEN_TRADES_)
            arrSymbol = [ok for ok in currencyList
                         if ok in openCurList]
            for cur in currencyList:
                if cur in arrSymbol:
                    continue
                _zmq._DWX_MTX_SEND_MARKETDATA_REQUEST_(_symbol=cur, _timeframe=240,
                                                       _start='2020.1.1', _end='2020.1.2')
                sleep(0.5)
                df_H4 = MT4.get_df()
                _zmq._DWX_MTX_SEND_MARKETDATA_REQUEST_(_symbol=cur, _timeframe=1440,
                                                       _start='2020.1.1', _end='2020.1.2')
                sleep(0.5)
                df_D1 = MT4.get_df()
                dir_H4 = MT4.trend_dir(df_H4)
                dir_D1 = MT4.trend_dir(df_D1)
                if (dir_H4 != dir_D1)or(dir_H4 == 0)or(dir_D1==0):
                    continue
                RSI = MT4.RSI(df_H4['Close'], len(df_H4['Close'])-1)
                if (RSI[0] > 70) or (RSI[0] < 30):
                    continue
                a, b = [], []
                for tf in timeframeList:
                    _zmq._DWX_MTX_SEND_MARKETDATA_REQUEST_(_symbol=cur, _timeframe=tf,
                                                       _start='2020.1.1', _end='2020.1.2')
                    sleep(2)
                    any_df = MT4.get_df()
                    m, v, a, b = MT4.get_m_v(a, b, any_df)
                if (df_H4['Tick_Vol'][0] < v) or (MT4.get_ength(df_H4) < m):
                    continue
                if dir_H4 < 0:
                    _my_trade['_type']=1
                    _my_trade['_symbol']=cur
                    _zmq._DWX_MTX_NEW_TRADE_(_order=_my_trade)
                    sleep(5)
                    oped = f_get(_zmq._SPI_ZMQ_GET_OPED_)
                    sleep(0.2)                    
                    break
                if dir_H4 > 0:
                    _my_trade['_type']=0
                    _my_trade['_symbol']=cur
                    _zmq._DWX_MTX_NEW_TRADE_(_order=_my_trade)
                    sleep(5)
                    oped = f_get(_zmq._SPI_ZMQ_GET_OPED_)
                    sleep(0.2)
                    break
                if (cur == 'NZDCAD') and (int(oped[0]) < 4):
                    return re_run(f_get(_zmq._SPI_ZMQ_GET_OPED_))
        return re_run(f_get(_zmq._SPI_ZMQ_GET_OPED_))
    except Exception as e:
        raise NameError(e.args)

#To wait changes
def re_run(oped):
    while (int(oped[0]) >= 4):
        print('Sleeping for 4 hour...')
        sleep(14400) #14400 for 4 hours
        oped = f_get(_zmq._SPI_ZMQ_GET_OPED_)
    if int(oped[0]) < 4:
        print('Sleeping for 1 hours...')
        sleep(3600)
        oped = f_get(_zmq._SPI_ZMQ_GET_OPED_)
    return run(oped)


currencyList = ['AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADCHF', 'CADJPY', 'CHFJPY', 'EURAUD', 'EURCAD',
                'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD', 'GBPCHF', 'GBPJPY', 'GBPUSD', 'NZDJPY', 'NZDUSD',
                'USDCAD', 'USDCHF', 'USDJPY', 'GBPAUD', 'GBPNZD', 'GBPCAD', 'NZDCHF', 'NZDCAD']
timeframeList = [1, 5, 15, 30, 60, 240, 1440, 10080]
origin_stdout = sys.stdout
_zmq = DWX_ZeroMQ_Connector()
_my_trade = _zmq._generate_default_order_dict()
_my_trade['_SL']=400
_my_trade['_TP']=600

if __name__ == "__main__":
    try:
        run(f_get(_zmq._SPI_ZMQ_GET_OPED_))
    except KeyboardInterrupt:
        sys.stdout = origin_stdout
        print('Ctrl+C: success')
    except NameError:
        raise
    finally:
        sys.stdout = origin_stdout
