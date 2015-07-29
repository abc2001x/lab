#coding=utf-8

from __future__ import absolute_import, division, print_function, with_statement

import socket

from tornado.escape import native_str
from myconnection import MyServerConnection
from tornado import gen
from tornado import iostream
from tornado.tcpserver import TCPServer
from tornado.util import Configurable
from tornado.log import gen_log, app_log

# class MyApplication(httputil.HTTPServerConnectionDelegate):
class MyApplication():

    def __init__(self,handlers):
        self.handlers = None
        if isinstance(handlers,dict):
            self.handlers = handlers

        

    def add_handler(self):
        pass

    """Implement this interface to handle requests from `.HTTPServer`.

    .. versionadded:: 4.0
    """
    def on_request(self, server_conn):
        """This method is called by the server when a new request has started.

        :arg server_conn: is an opaque object representing the long-lived
            (e.g. tcp-level) connection.
        :arg request_conn: is a `.HTTPConnection` object for a single
            request/response exchange.

        This method should return a `.HTTPMessageDelegate`.
        """
        return _RequestDispatcher(self, server_conn)

    def on_close(self, server_conn):
        """This method is called when a connection has been closed.

        :arg server_conn: is a server connection that has previously been
            passed to ``start_request``.
        """
        pass


# class _RequestDispatcher(httputil.HTTPMessageDelegate):
class _RequestDispatcher():
    """docstring for _RequestDispatcher"""
    def __init__(self, application,server_conn):
        self.application = application
        self.server_conn = server_conn
        self.request = None
        self.handler = None
        self.handler_kwargs = None

    def _find_handler(self):
        app = self.application
        if not app.handlers:
            #没有设置handler
            return
        if self.request in app.handlers.keys():
            self.handler = app.handlers[self.request]()
            setattr(self.handler, 'write', self.server_conn.write)
        else:
            app_log.error('no handler dispatch')
        return 

    def on_request(self,message):
        """Called when the HTTP headers have been received and parsed.

        :arg start_line: a `.RequestStartLine` or `.ResponseStartLine`
            depending on whether this is a client or server message.
        :arg headers: a `.HTTPHeaders` instance.

        Some `.HTTPConnection` methods can only be called during
        ``headers_received``.

        May return a `.Future`; if it does the body will not be read
        until it is done.
        """
        self.request = message
        self._find_handler()
        # return self._has_handler_instace()

    def _has_handler_instace(self):
        return bool(self.handler)

    def on_message(self,message):
        if self._has_handler_instace():
            return self.execute(message)
        else:
            return self.on_request(message)

    def execute(self,func_name):
        method = getattr(self.handler, func_name)
        return method()


    def finish(self):
        """Called after the last chunk of data has been received."""
        pass

    def on_connection_close(self):
        """Called if the connection is closed without finishing the request.

        If ``headers_received`` is called, either ``finish`` or
        ``on_connection_close`` will be called, but not both.
        """
        pass
		