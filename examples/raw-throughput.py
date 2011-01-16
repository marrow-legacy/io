# encoding: utf-8

"""An example raw marrow.io reactor example."""

from marrow.io.reactor import Reactor

try:
    range = xrange
except:
    pass


reactor = Reactor()
chunk = b"a" * 1024 * 4


@reactor.inline_callbacks
def serve(stream):
    request = yield stream.read(82)
    yield stream.write(b"HTTP/1.0 200 OK\r\nContent-Length: 4194304\r\n\r\n")
    
    for i in range(1024):
        yield stream.write(chunk)
    
    stream.close()


reactor.listen(('127.0.0.1', 8010), 1024, serve)
reactor.start()
