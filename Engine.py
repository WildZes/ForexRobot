from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector
from time import sleep
from io import StringIO
import sys
import MT4_calculations as MT4
from multiprocessing import Pool
from datetime import datetime as dt


def istime(value):
    try:
        dt.strptime(value, '%Y.%m.%d %H:%M:%S')
        return True
    except ValueError:
        return False


def isfloat(value):
    out = 0
    try:
      out = float(value)
      return True, out
    except ValueError:
      return False, out


def open_trades_by_symbol(symbol, slope, intercept, trend_direction, m, v):
    _my_trade['_symbol']=symbol
    if trend_direction < 0:
        _my_trade['_type']=1
        price_func = _zmq._SPI_ZMQ_GET_BID_
    elif trend_direction > 0:
        _my_trade['_type']=0
        price_func = _zmq._SPI_ZMQ_GET_ASK_
    else:
        raise NameError('trend_direction equals to zero: should be less or more than zero')
    _, price = mt4_recv(price_func, 'tick_price', symbol=symbol)
    tick_time = MT4.time_to_num(mt4_recv(_zmq._SPI_ZMQ_GET_TIME_, 'time'))
    while MT4.check_price(price, tick_time, slope, intercept):
        _, price = mt4_recv(price_func, 'tick_price', symbol=symbol)
        tick_time = MT4.time_to_num(mt4_recv(_zmq._SPI_ZMQ_GET_TIME_, 'time'))
    log_data = mt4_recv(_zmq._DWX_MTX_NEW_TRADE_, 'order', order_type=_my_trade)
    log_data = log_data.rstrip() + f'calc_m: {m}, calc_v: {v}, slope: {slope}, \
        intercept: {intercept}, symbol: {symbol}, tick_time: {tick_time}\n'
    file_add(log_data)


def create_pool_list(pendingSymbols, oped):
    resulting_list = []
    for element in pendingSymbols[:(maxTr-oped)]:
        cur_list = []
        cur_list.append(element["Symbol"])
        cur_list.append(element["Strength"])
        cur_list.append(element["Intercept"])
        cur_list.append(element["Trend_dir"])
        cur_list.append(element["Calc_m"])
        cur_list.append(element["Calc_v"])
        resulting_list.append(cur_list)
    return resulting_list

#Functionn to create followSymbol
def create_FS(arrSymbol):
    followSymbol = []
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
        _, _, _, m_H4, c_H4 = MT4.create_y_x_A_m_c(df_H4)
        if (dir_H4 != dir_D1)or(dir_H4 == 0)or(dir_D1==0):
            continue
        RSI = MT4.RSI(df_H4['Close'], len(df_H4['Close'])-1)
        if (RSI[0] > 70) or (RSI[0] < 30):
            continue
        _, ask = mt4_recv(_zmq._SPI_ZMQ_GET_ASK_, 'tick_price', symbol=cur)
        _, bid = mt4_recv(_zmq._SPI_ZMQ_GET_BID_, 'tick_price', symbol=cur)
        tick_time = MT4.time_to_num(mt4_recv(_zmq._SPI_ZMQ_GET_TIME_, 'time'))
        if (not MT4.check_price(ask, tick_time, m_H4, c_H4)) or \
           (not MT4.check_price(bid, tick_time, m_H4, c_H4)):
               continue
        if not MT4.traversal_fiveless(df_H4):
            continue
        a, b = [], []
        for tf in timeframeList:
            _zmq._DWX_MTX_SEND_MARKETDATA_REQUEST_(_symbol=cur, _timeframe=tf,
                                               _start='2020.1.1', _end='2020.1.2')
            sleep(2)
            any_df = MT4.get_df()
            m, v, a, b = MT4.get_m_v(a, b, any_df)
        if (df_H4['Tick_Vol'][1] < v) or (m_H4 < m):
            continue
        to_pending = {"Symbol": cur, "Strength": m_H4, "Intercept": c_H4, "Trend_dir": dir_H4,
                      "Volume": df_H4['Tick_Vol'][0], "Calc_m": m, "Calc_v": v}
        followSymbol.append(to_pending)
    return sorted(followSymbol, key=lambda k: (k["Strength"], k["Volume"]))


#Something to upgrade MT4 reply solution
def mt4_recv(command, command_type, order_type=None, symbol=None):
    for i in range(1000):
        if command_type == 'oped':
            oped = command()
            if not oped.isnumeric():
                continue
            return oped
        if command_type == 'open_trades':
            trades = command()
            if 'OPEN_TRADES' not in trades:
                continue
            return trades
        if command_type == 'tick_price':
            tp = command(_symbol=symbol)
            tp_bool, tp = isfloat(tp)
            if not tp_bool:
                continue
            return tp_bool, tp
        if command_type == 'time':
            tick_time = command()
            if not istime(tick_time):
                continue
            return tick_time
        if command_type == 'order':
            command(_order=order_type)
            sleep(5)
            return _zmq._myData
        print('Error to debug')
        


#Function to get oped as int and to get answer from MT4 as variable
def f_get(command, order_type=None, symbol=None):
    result = StringIO()
    sys.stdout = result
    if order_type == None and symbol == None:
        command()
    elif symbol == None:
        command(_order=order_type)
        sleep(5)
    else:
        command(_symbol=symbol)
    sleep(0.5)
    out = result.getvalue()
    sys.stdout = origin_stdout
    return out


#Function to change log file
def file_add(string_to_add):
    with open('OrderLog.txt', 'a') as my_file:
        my_file.write(string_to_add)


#On start (no open orders)
def run(oped):
    if int(oped) < maxTr:
        openCurList = mt4_recv(_zmq._DWX_MTX_GET_ALL_OPEN_TRADES_, 'open_trades')
        arrSymbol = [ok for ok in currencyList if ok in openCurList]
        followSymbol = create_FS(arrSymbol)
        if len(followSymbol) != 0:
            with Pool(len(followSymbol)) as p:
                p.starmap(open_trades_by_symbol, create_pool_list(followSymbol, int(oped)))
            oped = mt4_recv(_zmq._SPI_ZMQ_GET_OPED_, 'oped')
    return re_run(oped)


#To wait changes
def re_run(oped):
    if int(oped) < maxTr:
        print('Sleeping for 4 hours...')
        sleep(14400)
    while (int(oped) >= maxTr):
        print('Sleeping for 24 hours...')
        sleep(86400) #14400 for 4 hours
    oped = mt4_recv(_zmq._SPI_ZMQ_GET_OPED_, 'oped')
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
maxTr = 4

if __name__ == "__main__":
    try:
        run(mt4_recv(_zmq._SPI_ZMQ_GET_OPED_, 'oped'))
    except KeyboardInterrupt:
        sys.stdout = origin_stdout
        print('Ctrl+C: success')
    except NameError:
        raise
    finally:
        sys.stdout = origin_stdout
