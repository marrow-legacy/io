import sys

from marrow.io.reactor import SelectReactor


BLKSIZE = 32768

reactor = SelectReactor()

@reactor.inline_callbacks
def upload():
    print 'connecting'
    stream = yield reactor.connect(('127.0.0.1', 7008))
    print 'connected'
    with open(sys.argv[1], 'rb') as f:
        data = f.read(BLKSIZE)
        while data:
            print 'sending %d bytes' % len(data)
            sent = yield stream.write(data)
            print 'sent %d bytes' % sent
            data = f.read(BLKSIZE)

    stream.close()
    reactor.shutdown()

assert len(sys.argv) > 1
reactor.call_in_reactor(upload)
reactor.start()
