#!/usr/bin/env python
# encoding: utf-8

import os
import sys

from setuptools import setup, find_packages


if sys.version_info < (2, 6):
    raise SystemExit("Python 2.6 or later is required.")

exec(open(os.path.join("marrow", "io", "release.py")).read())



setup(
        name = name,
        version = version,
        
        description = "A stand-alone version of the Tornado IOLoop and IOStream implementations for those who don't want or need the full stack.",
        long_description = """\
For full documentation, see the README.textile file present in the package,
or view it online on the GitHub project page:

https://github.com/marrow/marrow.io""",
        
        author = "Alice Bevan-McGregor",
        author_email = "alice+marrow@gothcandy.com",
        url = "https://github.com/marrow/marrow.io",
        license = "Apache",
        
        install_requires = [
            'marrow.util < 2.0'
        ],
        
        test_suite = 'nose.collector',
        tests_require = [
            'nose',
            'coverage'
        ],
        
        classifiers = [
                "Development Status :: 5 - Production/Stable",
                "Environment :: Console",
                "Intended Audience :: Developers",
                "License :: OSI Approved :: Apache Software License",
                "Operating System :: OS Independent",
                "Programming Language :: Python",
                "Programming Language :: Python :: 2.6",
                "Programming Language :: Python :: 2.7",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.1",
                "Programming Language :: Python :: 3.2",
                "Topic :: Software Development :: Libraries :: Python Modules",
                "Topic :: System :: Networking",
                "Topic :: Utilities"
            ],
        
        packages = find_packages(exclude=['examples', 'tests']),
        zip_safe = True,
        include_package_data = True,
        package_data = {'': ['README.textile', 'LICENSE']},
        
        namespace_packages = ['marrow'],
    )
