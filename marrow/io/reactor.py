from Queue import Queue, Empty
from socket import (socket, error, AF_INET, SOCK_STREAM, SOCK_DGRAM,
                    SOL_SOCKET, SOL_TCP, SO_ERROR, TCP_NODELAY)
from errno import EINPROGRESS
from select import select
from threading import current_thread
from concurrent.futures import Future
from functools import partial, wraps
from types import GeneratorType
import sys
import os

from ioloop.stream import IOStream

try:
    from select import epoll, EPOLLIN, EPOLLOUT, EPOLLERR
except ImportError:
    epoll = None


class ReactorError(Exception):
    pass


class ReturnValue(object):
    def __init__(self, result):
        self.result = result


class ReactorBase(object):
    _shutdown = False
    _thread = None

    def __init__(self):
        self._call_queue = Queue()
        self._read_list = []
        self._read_callbacks = {}
        self._write_list = []
        self._write_callbacks = {}

        self._notify_recv_socket = socket(AF_INET, SOCK_DGRAM)
        self._notify_recv_socket.bind(('127.0.0.1', 0))
        self._notify_send_socket = socket(AF_INET, SOCK_DGRAM)
        self._notify_send_socket.connect(
            self._notify_recv_socket.getsockname())
        self._add_read_socket(self._notify_recv_socket, self._process_calls)

    def _add_read_socket(self, sock, callback):
        assert sock not in self._read_list
        self._read_list.append(sock)
        self._read_callbacks[sock] = callback

    def _add_write_socket(self, sock, callback):
        assert sock not in self._write_list
        self._write_list.append(sock)
        self._write_callbacks[sock] = callback

    def _remove_read_socket(self, sock):
        self._read_list.remove(sock)
        del self._read_callbacks[sock]

    def _remove_write_socket(self, sock):
        self._write_list.remove(sock)
        del self._write_callbacks[sock]

    def _process_calls(self):
        self._notify_recv_socket.recv(4096)
        while True:
            try:
                func, args, kwargs, future = self._call_queue.get(False)
            except Empty:
                return

            if future.set_running_or_notify_cancel():
                try:
                    result = func(*args, **kwargs)
                except Exception:
                    future.set_exception(sys.exc_info()[1])
                else:
                    future.set_result(result)

    def _inline_callbacks(self, g, future, temp_future=None):
        if temp_future:
            exc = temp_future.exception()
            if not exc:
                retval = temp_future.result()
        else:
            exc = retval = None

        while True:
            try:
                if exc:
                    retval = g.throw(exc)
                else:
                    retval = g.send(retval)
            except StopIteration:
                future.set_result(None)
                return
            except Exception:
                future.set_exception(sys.exc_info()[1])
                return

            if isinstance(retval, Future):
                cb = partial(self.call_in_reactor, self._inline_callbacks,
                             g, future)
                retval.add_done_callback(cb)
                return
            elif isinstance(retval, ReturnValue):
                future.set_result(retval.result)
                return

            exc = None

    @property
    def started(self):
        return self._thread is not None and not self._shutdown

    def shutdown(self):
        self.call_in_reactor(setattr, self, '_shutdown', True)

    def call_in_reactor(self, func, *args, **kwargs):
        future = Future()
        if current_thread() == self._thread:
            future.set_running_or_notify_cancel()
            try:
                result = func(*args, **kwargs)
            except Exception:
                future.set_exception(sys.exc_info()[1])
            else:
                future.set_result(result)
        else:
            self._call_queue.put((func, args, kwargs, future))
            self._notify_send_socket.send(b'\0')

        return future

    def inline_callbacks(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            future = Future()
            future.set_running_or_notify_cancel()
            try:
                g = self.call_in_reactor(func, *args, **kwargs).result()
            except Exception:
                future.set_exception(sys.exc_info()[1])
            else:
                if isinstance(g, GeneratorType):
                    self._inline_callbacks(g, future)
                else:
                    future.set_result(g)
            return future
        return inner

    def listen(self, addr, backlog, callback, family=AF_INET, type=SOCK_STREAM,
               proto=0):
        def _accept():
            sock = serv_sock.accept()[0]
            sock.setblocking(False)
            sock.setsockopt(SOL_TCP, TCP_NODELAY, 1)
            callback(IOStream(sock, self))

        serv_sock = socket(family, type, proto)
        serv_sock.setblocking(False)
        serv_sock.bind(addr)
        serv_sock.listen(backlog)
        self._add_read_socket(serv_sock, _accept)

    def connect(self, addr, family=AF_INET, type=SOCK_STREAM, proto=0):
        def _connect():
            self._remove_write_socket(sock)
            errcode = sock.getsockopt(SOL_SOCKET, SO_ERROR)
            if errcode:
                future.set_exception(error(errcode, os.strerror(errcode)))
            else:
                future.set_result(IOStream(sock, self))

        future = Future()
        future.set_running_or_notify_cancel()

        try:
            sock = socket(family, type, proto)
            sock.setblocking(False)
            errcode = sock.connect_ex(addr)
            if errcode != EINPROGRESS:
                raise error(errcode, os.strerror(errcode))
        except Exception:
            future.set_exception(sys.exc_info()[1])
        else:
            self._add_write_socket(sock, _connect)

        return future


class SelectReactor(ReactorBase):
    def __init__(self):
        self._exc_set = set()
        ReactorBase.__init__(self)

    def start(self):
        if self.started:
            raise ReactorError('The reactor has already been started')

        self._thread = current_thread()
        while not self._shutdown:
            rd, wr, ex = select(self._read_list, self._write_list,
                                self._exc_set)
            for sock in rd:
                self._read_callbacks[sock]()
            for sock in wr:
                self._write_callbacks[sock]()
            for sock in ex:
                read_cb = self._read_callbacks.get(sock)
                write_cb = self._write_callbacks.get(sock)
                if read_cb:
                    read_cb()
                if write_cb:
                    write_cb()

        # Cleanup
        self._notify_send_socket.close()
        self._notify_recv_socket.close()
        del self._read_list
        del self._read_callbacks
        del self._write_list
        del self._write_callbacks
        del self._exc_set

    def _add_read_socket(self, sock, callback):
        ReactorBase._add_read_socket(self, sock, callback)
        self._exc_set.add(sock)

    def _add_write_socket(self, sock, callback):
        ReactorBase._add_write_socket(self, sock, callback)
        self._exc_set.add(sock)

    def _remove_read_socket(self, sock):
        ReactorBase._remove_read_socket(self, sock)
        if not sock in self._write_list:
            self._exc_set.remove(sock)

    def _remove_write_socket(self, sock):
        ReactorBase._remove_read_socket(self, sock)
        if not sock in self._read_list:
            self._exc_set.remove(sock)


class EPollReactor(ReactorBase):
    READ_MASK = EPOLLIN | EPOLLERR
    WRITE_MASK = EPOLLOUT | EPOLLERR
    ALL_MASK = EPOLLIN | EPOLLOUT | EPOLLERR

    def __init__(self):
        self._epoll = epoll()
        self._read_map = {}
        self._write_map = {}
        ReactorBase.__init__(self)

    def start(self):
        if self.started:
            raise ReactorError('The reactor has already been started')

        self._thread = current_thread()
        while not self._shutdown:
            for fd, events in self._epoll.poll():
                if events & self.READ_MASK:
                    sock = self._read_map[fd]
                    self._read_callbacks[sock]()
                if events & self.WRITE_MASK:
                    sock = self._write_map[fd]
                    self._write_callbacks[sock]()

        # Cleanup
        self._notify_send_socket.close()
        self._notify_recv_socket.close()
        self._epoll.close()

    def _add_read_socket(self, sock, callback):
        ReactorBase._add_read_socket(self, sock, callback)
        if sock.fileno() not in self._read_map:
            self._epoll.register(sock, self.READ_MASK)
        else:
            self._epoll.modify(sock, self.ALL_MASK)
        self._read_map[sock.fileno()] = sock

    def _add_write_socket(self, sock, callback):
        ReactorBase._add_write_socket(self, sock, callback)
        if sock.fileno() not in self._write_map:
            self._epoll.register(sock, self.WRITE_MASK)
        else:
            self._epoll.modify(sock, self.ALL_MASK)
        self._write_map[sock.fileno()] = sock

    def _remove_read_socket(self, sock):
        ReactorBase._remove_read_socket(self, sock)
        if sock.fileno() not in self._write_map:
            self._epoll.unregister(sock)
        del self._read_map[sock.fileno()]

    def _remove_write_socket(self, sock):
        ReactorBase._remove_write_socket(self, sock)
        if sock.fileno() not in self._read_map:
            self._epoll.unregister(sock)
        del self._write_map[sock.fileno()]


# Determine the best default choice for the current platform
if epoll:
    Reactor = EPollReactor
else:
    Reactor = SelectReactor
