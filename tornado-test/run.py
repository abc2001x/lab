from myserver import MyServer
from tornado.ioloop import IOLoop
from tornado.log import gen_log, app_log
from myapplication import MyApplication

class TestHandler(object):
	"""docstring for TestHandler"""
	def __init__(self):
		super(TestHandler, self).__init__()

	def test(self):
		self.write('tesetsetsetes\r\n')
		app_log.error("tesetsetsetes")


app = MyApplication({'first':TestHandler})		

server = MyServer(app)
server.listen(8800)
IOLoop.current().start()
		