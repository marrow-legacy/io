#!/usr/bin/env python
# encoding: utf-8
import os

from distribute_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages


exec(open(os.path.join('marrow', 'io', 'version.py')))

setup(
    name='marrow.io',
    version=version,
    description='An I/O loop for asynchronous network applications',
    long_description=open('README.rst').read(),
    author='Alex Grönholm',
    author_email='alex.gronholm+pypi@nextday.fi',
    url='http://github.com/pulp/marrow.io',
    download_url='http://github.com/pulp/marrow.io/downloads',
    test_suite='nose.collector',
    tests_require=['nose', 'coverage'],
    
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: Utilities'
    ],
    
    packages=find_packages(exclude=['tests', 'tests.*', 'docs']),
    include_package_data=True,
    package_data={
        '': ['Makefile', 'README.rst', 'LICENSE', 'distribute_setup.py']
    },
    zip_safe=False,
    namespace_packages=['marrow'],
)
