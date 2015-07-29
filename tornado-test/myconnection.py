from __future__ import absolute_import, division, print_function, with_statement

import re

from tornado.concurrent import Future
from tornado.escape import native_str, utf8
from tornado import gen
from tornado import httputil
from tornado import iostream
from tornado.log import gen_log, app_log
from tornado import stack_context
from tornado.util import GzipDecompressor


class MyServerConnection(object):
    def __init__(self, stream, context=None):
        """
        :arg stream: an `.IOStream`
        :arg params: a `.HTTP1ConnectionParameters` or None
        :arg context: an opaque application-defined object that is accessible
            as ``connection.context``
        """
        self.stream = stream
        self.context = context
        self._serving_future = None

        self._serving_futures = []
        self._pending_writes = []

    @gen.coroutine
    def close(self):
        """Closes the connection.

        Returns a `.Future` that resolves after the serving loop has exited.
        """
        self.stream.close()
        # Block until the serving loop is done, but ignore any exceptions
        # (start_serving is already responsible for logging them).
        try:
            yield self._serving_future
        except Exception:
            pass

    def start_serving(self, delegate):
        """Starts serving requests on this connection.

        :arg delegate: a `.HTTPServerConnectionDelegate` start_request,on_close
        in this segement is myserver
        """
        # assert isinstance(delegate, httputil.HTTPServerConnectionDelegate)
        self._serving_future = self._server_request_loop(delegate)
        # Register the future on the IOLoop so its errors get logged.
        self.stream.io_loop.add_future(self._serving_future,
                                       lambda f: f.result())

    @gen.coroutine
    def read_message(self):
        message_future = self.stream.read_until_regex(b"\r?\n\r?\n")
        yield message_future




    @gen.coroutine
    def _server_request_loop(self, delegate):
        try:
            # from ipdb import set_trace
            # set_trace()
            request_delegate = delegate.on_request(self)

            while True:
                #get request adepter
                
                try:
                    message_future = self.stream.read_until_regex(b"\n\r?")
                    message = yield message_future
                    message = self._parse_data(message)
                except (iostream.StreamClosedError, iostream.UnsatisfiableReadError):
                    app_log.error("iostream.StreamClosedError, iostream.UnsatisfiableReadError")
                    self.close()
                    return
                except Exception:

                    gen_log.error("Uncaught exception", exc_info=True)
                    self.close()
                    return
                
                ret = request_delegate.on_message(message)
                if isinstance(ret, Future):
                    ret.add_done_callback(lambda f:self._serving_futures.remove(f))
                    self._serving_futures.append(ret)

                # conn = MyConnection(self.stream)
                # request_delegate = delegate.start_request(self, conn)
                # try:
                #     ret = yield conn.read_response(request_delegate)
                # except (iostream.StreamClosedError,
                #         iostream.UnsatisfiableReadError):
                #     return
                # except _QuietException:
                #     # This exception was already logged.
                #     conn.close()
                #     return
                # except Exception:
                #     gen_log.error("Uncaught exception", exc_info=True)
                #     conn.close()
                #     return
                # if not ret:
                #     return

                # if not self.header_received :
                #     self.header_received = True

                # yield gen.moment
        finally:
            delegate.on_close(self)
    def _parse_data(self, data):
        return native_str(data.decode('latin1')).strip(" \r\n")

    def write(self,chunk):
        _pending_write = self.stream.write(chunk)
        self._pending_writes.append(_pending_write)
        _pending_write.add_done_callback(lambda f:self._pending_writes.remove(f))

# class MyConnection(object):
#     """docstring for MyConnection"""
#     def __init__(self, stream):
#         self.stream = stream

#     def write():
#         pass

#     def close():
#         pass
    
#     @gen.concurrent
#     def read_header(self,delegate):
#         pass

#     @gen.concurrent
#     def read_response(self,delegate):
#         pass

