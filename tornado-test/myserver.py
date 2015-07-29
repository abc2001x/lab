#coding=utf-8

from __future__ import absolute_import, division, print_function, with_statement

import socket

from tornado.escape import native_str
from myconnection import MyServerConnection
from tornado import gen
from tornado import iostream
from tornado.tcpserver import TCPServer
from tornado.util import Configurable


class MyServer(TCPServer, Configurable):
    
    def __init__(self, *args, **kwargs):
        # Ignore args to __init__; real initialization belongs in
        # initialize since we're Configurable. (there's something
        # weird in initialization order between this class,
        # Configurable, and TCPServer so we can't leave __init__ out
        # completely)
        pass

    def initialize(self, request_callback,io_loop=None,
                   chunk_size=None, max_header_size=None, max_buffer_size=None):
        
        self.request_callback = request_callback

        TCPServer.__init__(self, io_loop=io_loop,
                           max_buffer_size=max_buffer_size,
                           read_chunk_size=chunk_size)
        self._connections = set()

    @classmethod
    def configurable_base(cls):
        return MyServer

    @classmethod
    def configurable_default(cls):
        return MyServer

    #建立连接后的回调
    def handle_stream(self, stream, address):
        # context = _HTTPRequestContext(stream, address,
        #                               self.protocol)
        conn = MyServerConnection(stream)
        self._connections.add(conn)
        conn.start_serving(self)

    def on_request(self, server_conn):
        # return 'start request....'
        return _ServerRequestAdapter(self, server_conn)

    def on_close(self, server_conn):
        self._connections.remove(server_conn)


class _ServerRequestAdapter(object):
    def __init__(self, server, server_conn):
        self.server = server
        self.connection = server_conn
        self.request = None
        self.delegate = server.request_callback.on_request(server_conn)
        # if isinstance(server.request_callback,
        #               httputil.HTTPServerConnectionDelegate):
        #     self.delegate = server.request_callback.start_request(
        #         server_conn, request_conn)
        #     self._chunks = None
        # else:
        #     self.delegate = None
        #     self._chunks = []



    def on_message(self,message):
        return self.delegate.on_message(message)
        

    def finish(self):
        """Called after the last chunk of data has been received."""
        pass

    def on_connection_close(self):
        """Called if the connection is closed without finishing the request.

        If ``headers_received`` is called, either ``finish`` or
        ``on_connection_close`` will be called, but not both.
        """
        pass
		