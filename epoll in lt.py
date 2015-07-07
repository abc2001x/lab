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

#创建epoll对象,epoll对象是个存储"fd-事件"的容器,把关注的"fd-事件"注册到容器中,
#接下来就可以监听到fd的事件
epoll = select.epoll()

#将server的sockect注册到epoll中,因为此示例程序功能是浏览器显示helloword,
#所以关注接入的客户端fd,当有客户端连接时,出发的一定是server sockect的EPOLLIN
epoll.register(serversocket.fileno(), select.EPOLLIN)

try:
   connections = {}; requests = {}; responses = {}
   while True:
      events = epoll.poll(10)
      # print '=='*10
      for fileno, event in events:
         #客户端接入时,注册客户端fd到epoll,第一步需要读取客户端发送到服务端的信息,所以用EPOLLIN
         if fileno == serversocket.fileno():
            connection, address = serversocket.accept()
            connection.setblocking(0)
            epoll.register(connection.fileno(), select.EPOLLIN)
            connections[connection.fileno()] = connection
            requests[connection.fileno()] = b''
            responses[connection.fileno()] = response
         #读取客户端信息
         elif event & select.EPOLLIN:
            data=connections[fileno].recv(1024)

            requests[fileno] += data
            #判断客户端信息是否读取完毕
            if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
               epoll.modify(fileno, select.EPOLLOUT)
               print('-'*40 + str(fileno) + '\n' + requests[fileno].decode()[:-2])
            #处理客户端关闭请求时的信息,防止服务端程序出现close_wait
            #使用telnet测试后发现,客户端主动关闭时会发送个空信息到客户端,不处理的话,会出现close_wait,
            #并且循环中每次都会出现该事件,会严重影响程序处理效率,因此需要把它从epoll重移除
            if data == b'':
               print "receiv client close : %s "% str(fileno)
               epoll.unregister(fileno)
               try :
                  connections[fileno].close()
               except Exception, e:
                  print ' connection was allready closed.....'+e
         #将此接入返回给客户端
         elif event & select.EPOLLOUT:
            byteswritten = connections[fileno].send(responses[fileno])
            responses[fileno] = responses[fileno][byteswritten:]
            if len(responses[fileno]) == 0:
               epoll.modify(fileno, 0)
               try:
                  connections[fileno].shutdown(socket.SHUT_RDWR)
               except Exception, e:
                  print ' connection was allready closed.....' + e
         #服务端主动关闭连接时的逻辑处理
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