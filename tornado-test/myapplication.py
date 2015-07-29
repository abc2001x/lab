#coding=utf-8

from __future__ import absolute_import, division, print_function, with_statement

from tornado.escape import native_str
from myconnection import MyServerConnection
from tornado import stack_context
from tornado.log import app_log
from inspect import getmembers
# class MyApplication(httputil.HTTPServerConnectionDelegate):
class MyApplication():

    def __init__(self,handlers):
        self.handlers = None
        if isinstance(handlers,dict):
            self.handlers = handlers

    def on_request(self, server_conn):
        return _RequestDispatcher(self, server_conn)


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
            setattr(self.handler, 'close', self.close)
            
            method_list = getmembers(self.handler)
            app_log.info(' found the handler,enter the method name to execute \n list:%s'%method_list)

        else:
            app_log.error(' no handler dispatch,please enter handler\'s name again')
        return 

    def on_request(self,message):
        
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
        exec_method = None
        try:
            exec_method = getattr(self.handler, func_name)
            exec_method = stack_context.wrap(exec_method)
        except Exception, e:
            app_log.error(' no exist method to call')
        
        if exec_method:
            return exec_method()
            
    def close(self):
        self.server_conn.close()
		