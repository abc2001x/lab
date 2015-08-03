#coding=utf-8
#
from __future__ import absolute_import, division, print_function, with_statement


from tornado.concurrent import Future
from tornado.escape import native_str, utf8
from tornado import gen
from tornado import iostream
from tornado.log import gen_log, app_log
from tornado.util import GzipDecompressor


class MyServerConnection(object):
    def __init__(self, stream):
        self.stream = stream

        self._serving_futures = []
        self._pending_writes = []

    def close(self):

        def mayby_close(f):
            futures = self._serving_futures+self._pending_writes
            app_log.error(futures)
            if not any(futures):
                self.stream.close()

        pending_futrues = self._serving_futures+self._pending_writes
        if any(pending_futrues):
            map(lambda f:f.add_done_callback(mayby_close),pending_futrues)
        else:
            self.stream.close()
        

    def start_serving(self, delegate):
        self._serving_future = self._server_request_loop(delegate)

        self.stream.io_loop.add_future(self._serving_future,
                                       lambda f: f.result())

    @gen.coroutine
    def _server_request_loop(self, delegate):
        try:
            #get request adepter
            request_delegate = delegate.on_request(self)
            while True:
                
                try:
                    message_future = self.stream.read_until_regex(b"\n\r?")
                    message = yield message_future
                    message = self._parse_data(message)

                except (iostream.StreamClosedError, 
                        iostream.UnsatisfiableReadError):
                    app_log.error(' close the connect')
                    self.close()
                    return

                except Exception:

                    gen_log.error("Uncaught exception", exc_info=True)
                    self.close()
                    return
                
                ret = request_delegate.on_message(message)
                #如果是异步执行的方法,保存future,用于确保close时,所有future都已完成
                if isinstance(ret, Future):
                    ret.add_done_callback(lambda f:self._serving_futures.remove(f))
                    self._serving_futures.append(ret)

        finally:
            delegate.on_close(self)
    
    def _parse_data(self, data):
        return native_str(data.decode('latin1')).strip(" \r\n")

    def write(self,chunk):
        _pending_write = self.stream.write(chunk)
        self._pending_writes.append(_pending_write)
        _pending_write.add_done_callback(lambda f:self._pending_writes.remove(f))
