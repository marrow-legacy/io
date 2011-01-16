#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function

import sys
import cProfile
import signal
import subprocess
import logging
import socket

from marrow.util.compat import exception
from marrow.script import script, describe, execute
from marrow.io.reactor import Reactor, SelectReactor

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
            reactor = Reactor()
        
        elif select and epoll:
            print("Can't set both epoll and select reactors for simultaneous use!")
            return
        
        elif select:
            reactor = SelectReactor()
        
        elif epoll:
            if EPollReactor is None:
                print("EPollReactor not available!")
                return
            
            reactor = EPollReactor()
        
        clength = size * 1024
        bsize = block * 1024
        chunk = b"a" * bsize
        
        print("Content-Length: %d\nChunk-Size: %d\nIterations: %d" % (clength, bsize, clength / bsize))
        
        @reactor.inline_callbacks
        def serve(stream):
            request = yield stream.read(82)
            
            yield stream.write(b"HTTP/1.0 200 OK\r\nContent-Length: %d\r\n\r\n" % (clength, ))
            
            for i in range(clength / bsize):
                yield stream.write(chunk)
            
            stream.close()
        
        reactor.listen(('127.0.0.1', 8010), 1024, serve)
        
        def handle_sigchld(sig, frame):
            reactor.shutdown()
        
        signal.signal(signal.SIGCHLD, handle_sigchld)
        
        proc = subprocess.Popen("ab -n %d -c %d http://127.0.0.1:8010/ | grep \"Transfer rate\"" % (number, concurrency), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            reactor.start()
        except KeyboardInterrupt:
            print("\nKilled by user request.")
            try:
                reactor._sock.close()
            except:
                pass
        except:
            try:
                reactor._sock.close()
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
