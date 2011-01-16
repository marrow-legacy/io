#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function

import sys
import cProfile
import signal
import subprocess
import logging
import socket
import select as _select

from marrow.util.compat import exception
from marrow.script import script, describe, execute
from marrow.io import ioloop

try:
    from marrow.io.reactor import EPollReactor
except ImportError:
    EPollReactor = None

try:
    range = xrange
except:
    pass



def hello(request):
    yield b'200 OK', [(b'Content-Length', b'13'), (b'Content-Type', b'text/plain')]
    yield b'Hello world!\n'


@script(
        title="Marrow HTTPD Benchmark",
        version="1.0",
        copyright="Copyright 2010 Alice Bevan-McGregor"
    )
@describe(
        number="The number of requests to run, defaults to 10.",
        concurrency="The level of concurrency, defaults to 1.",
        profile="If enabled, profiling results will be saved to \"results.prof\".",
        verbose="Increase the logging level from INFO to DEBUG.",
        size="Size of the returned data, in KiB, defaults to 4 MiB.",
        block="The size of the chunks, in KiB, defaults to 1 MiB; must evenly go into size.",
        select="Force use of the select reactor.",
        epoll="Force use of the epoll reactor."
    )
def main(number=10, concurrency=1, profile=False, verbose=False, size=4096, block=1024, select=False, epoll=False):
    """A simple benchmark of marrow.io.
    
    This script requires that ApacheBench (ab) be installed.
    
    If profiling is enabled, you can examine the results by running:
    
    python -c 'import pstats; pstats.Stats("nXcY.prof").strip_dirs().sort_stats("time").print_callers(20)'
    """
    
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    
    def do():
        if not select and not epoll:
            pass
        
        elif select and epoll:
            print("Can't set both epoll and select reactors for simultaneous use!")
            return
        
        elif select:
            ioloop._poll = ioloop._Select
        
        elif epoll:
            try:
                ioloop._poll = _select.epoll
            except:
                print("EPoll not available.")
                return
        
        clength = size * 1024
        bsize = block * 1024
        chunk = b"a" * bsize
        nchunks = clength / bsize
        
        print("Content-Length: %d\nChunk-Size: %d\nIterations: %d" % (clength, bsize, nchunks))
        
        def connection_ready(sock, fd, events):
            while True:
                try:
                    connection, address = sock.accept()
                
                except socket.error:
                    exc = exception().exception
                    if exc.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                        raise
                    
                    return
                
                connection.setblocking(0)
                stream = iostream.IOStream(connection)
                
                def read_request(stream, request):
                    def write_chunk(stream, chunks_written=0):
                        if chunks_written == nchunks:
                            stream.close()
                            return
                        
                        stream.write(chunk, functools.partial(write_chunk, stream, chunks_written+1))
                    
                    stream.write(b"HTTP/1.0 200 OK\r\nContent-Length: %s\r\n\r\n" % (clength, ), functools.partial(write_chunk, stream))
                
                stream.read(82, functools.partial(read_request, stream)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(0)
        sock.bind(("", 8010))
        sock.listen(5000)
        
        io_loop = ioloop.IOLoop.instance()
        io_loop.set_blocking_log_threshold(2)
        callback = functools.partial(connection_ready, sock)
        io_loop.add_handler(sock.fileno(), callback, io_loop.READ)
        
        def handle_sigchld(sig, frame):
            reactor.shutdown()
        
        signal.signal(signal.SIGCHLD, handle_sigchld)
        
        proc = subprocess.Popen("ab -n %d -c %d http://127.0.0.1:8010/ | grep \"Transfer rate\"" % (number, concurrency), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            io_loop.start()
        except KeyboardInterrupt:
            print("\nKilled by user request.")
            try:
                io_loop.stop()
            except:
                pass
        except:
            try:
                io_loop.stop()
            except:
                pass
            
            exc = exception()
            ok = False
            
            try:
                if exc.args[0] == 4:
                    ok = True # Eat "Interrupted system call"
            except: pass
            
            if not ok:
                logging.exception("Recieved exception.")
        
        stdout, stderr = proc.communicate()
        
        try:
            rate = float(stdout.split("\n")[0].split()[2].strip())
            print("Result: %s %d/%d KiB, %dR C%d = %0.2f MiB/s" % (reactor.__class__.__name__, size, block, number, concurrency, rate / 1024.0))
        
        except:
            print("\nApacheBench STDERR:\n%s\n\nApacheBench STDOUT:\n%s" % (stderr, stdout))
        
        # Transfer rate:          686506.82 [Kbytes/sec] received
    
    try:
        if not profile:
            do()
        
        else:
            cProfile.runctx('do()', globals(), locals(), 'n%dc%d.prof' % (number, concurrency))
            print("\nProfiling results written to: %s\n" % ('n%dc%d.prof' % (number, concurrency)))
    
    except KeyboardInterrupt:
        print("\nBenchmark cancelled.\n")



if __name__ == '__main__':
    execute(main)
