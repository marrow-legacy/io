# encoding: utf-8

"""An example raw marrow.io reactor example."""

from marrow.io.reactor import Reactor

try:
    range = xrange
except:
    pass


reactor = Reactor()
chunk = b"a" * 4096


@reactor.inline_callbacks
def serve(stream):
    yield stream.write(b"HTTP/1.0 200 OK\r\nContent-Length: 4194304\r\n\r\n")
    
    # Send 4MiB of data, 4KiB at a time.
    for i in range(1024):
        yield stream.write(chunk)
    
    stream.close()


reactor.listen(('127.0.0.1', 8010), 1024, serve)
reactor.start()
