from concurrent.futures import Future
from io import BytesIO
from socket import MSG_PEEK
import sys


class StreamException(Exception):
    pass


class IOStream(object):
    __slots__ = '_socket', '_reactor',  '_read_future', '_write_future'

    def __init__(self, socket, reactor):
        self._socket = socket
        self._reactor = reactor
        self._read_future = None
        self._write_future = None

    def _read_result(self, result=None, exception=None):
        self._reactor._remove_read_socket(self._socket)
        future = self._read_future
        self._read_future = None
        if exception:
            future.set_exception(sys.exc_info()[1])
        else:
            future.set_result(result)

    def _write_result(self, result=None, exception=None):
        self._reactor._remove_write_socket(self._socket)
        future = self._write_future
        self._write_future = None
        if exception:
            future.set_exception(sys.exc_info()[1])
        else:
            future.set_result(result)

    def read(self, num_bytes):
        def _read():
            try:
                data = self._socket.recv(bytes_left[0])
            except Exception:
                self._read_result(exception=sys.exc_info()[1])
                return

            buffer.write(data)
            bytes_left[0] -= len(data)
            if len(data) == 0 or bytes_left[0] == 0:
                self._read_result(buffer.getvalue())

        if self._read_future:
            raise StreamException('Already reading from this socket')

        bytes_left = [num_bytes]
        buffer = BytesIO()
        self._read_future = Future()
        self._read_future.set_running_or_notify_cancel()
        self._reactor._add_read_socket(self._socket, _read)
        return self._read_future

    def read_until(self, delimiter, read_chunk=8192, max_buffer_size=104857600):
        def _read():
            try:
                data = self._socket.recv(read_chunk, MSG_PEEK)
            except Exception:
                self._read_result(exception=sys.exc_info()[1])

            if len(data) == 0:
                self._read_result(buffer.getvalue())

            pos = buffer.getvalue().index(delimiter)
            if pos >= 0:
                self._socket.recv(pos + len(delimiter))
                buffer.write(data[:pos + 1])
                self._read_result(buffer.getvalue())
            else:
                self._socket.recv(read_chunk)
                buffer.write(data)

        if self._read_future:
            raise StreamException('Already reading from this socket')

        buffer = BytesIO()
        self._read_future = Future()
        self._read_future.set_running_or_notify_cancel()
        self._reactor._add_read_socket(self._socket, _read)
        return self._read_future

    def write(self, data):
        def _write():
            try:
                written = self._socket.send(data[pos[0]:])
            except Exception:
                self._write_result(exception=sys.exc_info()[1])
            else:
                pos[0] += written
                if written == 0 or pos[0] == len(data):
                    self._write_result(pos[0])

        if self._write_future:
            raise StreamException('Already writing to this socket')

        pos = [0]
        self._write_future = Future()
        self._write_future.set_running_or_notify_cancel()
        self._reactor._add_write_socket(self._socket, _write)
        return self._write_future

    def close(self):
        self._socket.close()
