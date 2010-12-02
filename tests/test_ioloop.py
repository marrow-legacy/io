# encoding: utf-8

from __future__ import unicode_literals

import time
import socket

from unittest import TestCase
from functools import partial

from marrow.io.iostream import IOStream
from marrow.io.testing import AsyncTestCase


log = __import__('logging').getLogger(__name__)



class TestIOLoop(AsyncTestCase):
    def __init__(self, *args, **kw):
        self.called = False
        super(TestIOLoop, self).__init__(*args, **kw)
    
    def test_add_callback_wakeup(self):
        # Make sure that add_callback from inside a running IOLoop
        # wakes up the IOLoop immediately instead of waiting for a timeout.
        def callback():
            self.called = True
            self.stop()
        
        def schedule_callback():
            self.called = False
            self.io_loop.add_callback(callback)
            # Store away the time so we can check if we woke up immediately
            self.start_time = time.time()
        
        self.io_loop.add_timeout(time.time(), schedule_callback)
        self.wait()
        self.assertAlmostEqual(time.time(), self.start_time, places=2)
        self.assertTrue(self.called)
    
    def test_exception_in_callback(self):
        self.io_loop.add_callback(lambda: 1/0)
        
        try:
            self.wait()
            self.fail("did not get expected exception")
        
        except ZeroDivisionError:
            pass
