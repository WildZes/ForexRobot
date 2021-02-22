from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector

if __name__ == "__main__":
    try:
        while True:
            continue
    except KeyboardInterrupt:
        pass
    _zmq = DWX_ZeroMQ_Connector()
    oped = _zmq._DWX_MTX_GET_ALL_OPEN_TRADES_()
