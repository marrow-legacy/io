# encoding: utf-8

"""An example raw marrow.io reactor example."""

from marrow.io.reactor import Reactor


reactor = Reactor()

@reactor.inline_callbacks
def serve(stream):
    yield stream.write(b"HTTP/1.0 200 OK\r\nContent-Length: 7\r\n\r\nPong!\r\n")
    stream.close()

reactor.listen(('127.0.0.1', 8010), 5, serve)
reactor.start()
