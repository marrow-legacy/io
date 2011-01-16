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
from marrow.io.reactor import Reactor

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
        requests="The number of requests to run, defaults to 10.",
        concurrency="The level of concurrency, defaults to 1.",
        profile="If enabled, profiling results will be saved to \"results.prof\".",
        verbose="Increase the logging level from INFO to DEBUG."
    )
def main(requests=10, concurrency=1, profile=False, verbose=False):
    """A simple benchmark of marrow.io.
    
    This script requires that ApacheBench (ab) be installed.
    
    If profiling is enabled, you can examine the results by running:
    
    python -c 'import pstats; pstats.Stats("nXcY.prof").strip_dirs().sort_stats("time").print_callers(20)'
    """
    
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    
    def do():
        reactor = Reactor()
        chunk = b"a" * 1024 * 1024
        
        @reactor.inline_callbacks
        def serve(stream):
            yield stream.write(b"HTTP/1.0 200 OK\r\nContent-Length: 4194304\r\n\r\n")
            
            for i in range(4):
                yield stream.write(chunk)
            
            stream.close()
        
        reactor.listen(('127.0.0.1', 8010), 1024, serve)
        
        def handle_sigchld(sig, frame):
            reactor.shutdown()
        
        signal.signal(signal.SIGCHLD, handle_sigchld)
        
        proc = subprocess.Popen("ab -n %d -c %d http://127.0.0.1:8010/ | grep \"Transfer rate\"" % (requests, concurrency), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            reactor.start()
        except:
            try:
                reactor._sock.close()
            except:
                pass
            
            exc = exception()
            
            if exc.args[0] == 4:
                pass # Eat "Interrupted system call"
            
            else:
                logging.exception("Recieved exception.")
        
        stdout, stderr = proc.communicate()
        
        try:
            rate = float(stdout.split("\n")[0].split()[2].strip())
            print("%dR C%d = %0.2f MiB/s" % (requests, concurrency, rate / 1024.0))
        
        except:
            print("ApacheBench STDERR:\n%s\n\nApacheBench STDOUT:\n%s" % (stderr, stdout))
        
        # Transfer rate:          686506.82 [Kbytes/sec] received
    
    try:
        if not profile:
            do()
        
        else:
            cProfile.runctx('do()', globals(), locals(), 'n%dc%d.prof' % (requests, concurrency))
            print("\nProfiling results written to: %s\n" % ('n%dc%d.prof' % (requests, concurrency)))
    
    except KeyboardInterrupt:
        print("\nBenchmark cancelled.\n")



if __name__ == '__main__':
    execute(main)
