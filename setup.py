#!/usr/bin/env python
# encoding: utf-8

import sys, os

try:
    from distribute_setup import use_setuptools
    use_setuptools()

except ImportError:
    pass

from setuptools import setup, find_packages, Extension


if sys.version_info <= (2, 6):
    raise SystemExit("Python 2.6 or later is required.")

if sys.version_info >= (3,0):
    def execfile(filename, globals_=None, locals_=None):
        if globals_ is None:
            globals_ = globals()
        
        if locals_ is None:
            locals_ = globals_
        
        exec(compile(open(filename).read(), filename, 'exec'), globals_, locals_)

else:
    from __builtin__ import execfile

execfile(os.path.join("marrow", "io", "release.py"), globals(), locals())


# Build the epoll extension for Linux systems with Python < 2.6.
# NOTE: 2.6 is the minimum version now.
# extensions = []
# 
# if "linux" in sys.platform.lower() and sys.version_info <= (2, 6):
#     extensions.append(Extension("marrow.io.epoll", ["marrow/io/epoll.c"]))


setup(
        name = name,
        version = version,
        
        description = summary,
        long_description = description,
        author = author,
        author_email = email,
        url = url,
        download_url = download_url,
        license = license,
        keywords = '',
        
        use_2to3 = True,
        install_requires = [],
        
        test_suite = 'nose.collector',
        tests_require = ['nose', 'coverage', 'nose-achievements'],
        
        classifiers = [
                "Development Status :: 5 - Production/Stable",
                "Environment :: Console",
                "Intended Audience :: Developers",
                "License :: OSI Approved :: Apache Software License",
                "Operating System :: OS Independent",
                "Programming Language :: Python",
                "Topic :: Software Development :: Libraries :: Python Modules"
            ],
        
        packages = find_packages(exclude=['tests', 'tests.*', 'docs']),
        include_package_data = True,
        package_data = {
                '': ['Makefile', 'README.textile', 'LICENSE', 'distribute_setup.py']
            },
        zip_safe = True,
        
        namespace_packages = ['marrow'],
    )
