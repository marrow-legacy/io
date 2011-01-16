from ioloop.reactor import Reactor


reactor = Reactor()

@reactor.inline_callbacks
def serve(stream):
    num_bytes = 0
    data = yield stream.read(4096)
    with open('uploaded.dat', 'wb') as f:
        while data:
            f.write(data)
            num_bytes += len(data)
            data = yield stream.read(4096)
    
    print 'received a file of %d bytes' % num_bytes

reactor.listen(('127.0.0.1', 7008), 5, serve)
reactor.start()
