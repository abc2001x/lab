from myserver import MyServer
from tornado.ioloop import IOLoop
from tornado.log import gen_log, app_log
from myapplication import MyApplication
from tornado.web import RequestHandler
from tornado.httpclient import AsyncHTTPClient
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.gen import coroutine

class Helloworld(RequestHandler):
	"""docstring for Helloworld"""
	
	def get(self):
		def hello_finish():
			self.write('hello world~~')
			self.finish()

		self._auto_finish = False
		iol = IOLoop.current()
		iol.add_timeout(iol.time()+10,hello_finish)


class TestHandler(object):
	"""docstring for TestHandler"""
	def __init__(self):
		super(TestHandler, self).__init__()

	@coroutine	
	def test(self):
		client = AsyncHTTPClient()
		yield client.fetch("http://localhost:8000/")
		
		self.write(' respone message\r\n')

if __name__ == '__main__':
	
	app1 = Application([('/',Helloworld)])
	server1 = HTTPServer(app1)
	server1.listen(8000)

	app = MyApplication({'first':TestHandler})
	server = MyServer(app)
	server.listen(8800)
	
	IOLoop.current().start()
			