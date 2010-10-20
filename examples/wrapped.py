# encoding: utf-8

"""An example IOLoop/IOStream example, simplified version of the raw example."""


from marrow.server.base import Server
from marrow.server.protocol import Protocol



class HTTPResponse(Protocol):
    def accept(self, client):
        self.server.respond(client, "HTTP/1.0 200 OK\r\nContent-Length: 5\r\n\r\nPong!\r\n", client.close)


if __name__ == '__main__':
    Server(None, 8010, HTTPResponse).start()
