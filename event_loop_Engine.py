import Engine as E


def elerun(oped):
    if int(oped) < E.maxTr:
        openCurList = E.mt4_recv(E._zmq._DWX_MTX_GET_ALL_OPEN_TRADES_, 'open_trades')
        arrSymbol = [ok for ok in E.currencyList if ok in openCurList]
        followSymbol = E.create_FS(arrSymbol)
        if len(followSymbol) != 0:
            with E.Pool(len(followSymbol)) as p:
                p.starmap(E.open_trades_by_symbol, E.create_pool_list(followSymbol, int(oped)))
            oped = E.mt4_recv(E._zmq._SPI_ZMQ_GET_OPED_, 'oped')


if __name__ == "__main__":
    while True:
        start_time = E.time()
        try:
            elerun(E.mt4_recv(E._zmq._SPI_ZMQ_GET_OPED_, 'oped'))
        except KeyboardInterrupt:
            E.sys.stdout = E.origin_stdout
            print('Ctrl+C: success')
            break
        except NameError as err:
            E.file_add(E.strftime('%Y-%m-%d %H:%M:%S', E.localtime(start_time)) + ': ' +  str(err) + '\n')
            continue
        finally:
            E.sys.stdout = E.origin_stdout
        end_time = E.time()
        if end_time - start_time > 3600:
            continue
        if int(E.mt4_recv(E._zmq._SPI_ZMQ_GET_OPED_, 'oped')) < E.maxTr:
            print('Sleeping for 4 hours...')
            E.file_add(E.strftime('%Y-%m-%d %H:%M:%S', E.localtime(E.time())) + ': ' + 'Sleeping for 4 hours...\n')
            E.sleep(14400)
        while (int(E.mt4_recv(E._zmq._SPI_ZMQ_GET_OPED_, 'oped')) >= E.maxTr):
            print('Sleeping for 24 hours...')
            E.file_add(E.strftime('%Y-%m-%d %H:%M:%S', E.localtime(E.time())) + ': ' + 'Sleeping for 24 hours...\n')
            E.sleep(86400)