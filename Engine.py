from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector
import sys
from io import StringIO
from time import sleep


#Function to get oped as int
def foped():
    try:
        sys.stdout = result
        _zmq._SPI_ZMQ_GET_OPED_()
        sleep(0.2)
        out = result.getvalue()
        sys.stdout = origin_stdout
        return int(out)
    except Exception as e:
        return e.args


#On start (no open orders)
def run(open_orders):
    if ~isinstance(open_orders, int):
        raise NameError(open_orders)
    while open_orders < 4:
        pass
    re_run()

#To wait changes
def re_run():
    sleep(1440)
    run(foped())


currencyList = ['AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADCHF', 'CADJPY', 'CHFJPY', 'EURAUD', 'EURCAD',
                'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD', 'GBPCHF', 'GBPJPY', 'GBPUSD', 'NZDJPY', 'NZDUSD',
                'USDCAD', 'USDCHF', 'USDJPY', 'GBPAUD', 'GBPNZD', 'GBPCAD', 'NZDCHF', 'NZDCAD']
timeframeList = ['1', '5', '15', '30', '60', '240', '1440', '10080']
origin_stdout = sys.stdout
result = StringIO()
_zmq = DWX_ZeroMQ_Connector()
oped = foped()

if __name__ == "__main__":
    try:
        run(foped())
    except KeyboardInterrupt:
        sys.stdout = origin_stdout
    except NameError:
        raise
    finally:
        sys.stdout = origin_stdout