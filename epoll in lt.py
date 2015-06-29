# coding: utf-8
import socket, select
from ipdb import set_trace
EOL1 = b'\n\n'
EOL2 = b'\n\r\n'
response  = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
response += b'Hello, world!'

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(('0.0.0.0', 8080))
serversocket.listen(10240)
serversocket.setblocking(0)
serversocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

epoll = select.epoll()
epoll.register(serversocket.fileno(), select.EPOLLIN)

try:
   connections = {}; requests = {}; responses = {}
   while True:
      events = epoll.poll(10)
      # print '=='*10
      for fileno, event in events:
         if fileno == serversocket.fileno():
            connection, address = serversocket.accept()
            connection.setblocking(0)
            epoll.register(connection.fileno(), select.EPOLLIN)
            connections[connection.fileno()] = connection
            requests[connection.fileno()] = b''
            responses[connection.fileno()] = response
         elif event & select.EPOLLIN:
            data=connections[fileno].recv(1024)

            requests[fileno] += data
            if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
               epoll.modify(fileno, select.EPOLLOUT)
               print('-'*40 + str(fileno) + '\n' + requests[fileno].decode()[:-2])
            #
            if data == b'':
               # set_trace()处理客户端关闭请求时的信息,防止服务端程序出现close_wait
               print "receiv client close : %s "% str(fileno)
               epoll.unregister(fileno)
               try :
                  connections[fileno].close()
               except Exception, e:
                  print ' connection was allready closed.....'+e
               

         elif event & select.EPOLLOUT:
            byteswritten = connections[fileno].send(responses[fileno])
            responses[fileno] = responses[fileno][byteswritten:]
            if len(responses[fileno]) == 0:
               epoll.modify(fileno, 0)
               try:
                  connections[fileno].shutdown(socket.SHUT_RDWR)
               except Exception, e:
                  print ' connection was allready closed.....' + e
               
         elif event & select.EPOLLHUP:
            print "close fd : %s "% str(fileno)
            epoll.unregister(fileno)
            connections[fileno].close()
            del connections[fileno]
         else :
            print '='*10
            print fileno,event
finally:
   # set_trace()
   epoll.unregister(serversocket.fileno())
   epoll.close()
   serversocket.close()
