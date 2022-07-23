from setuptools import setup, find_packages
import os

setup(
    name         = "openpower-pel-parsers",
    version      = os.getenv('PELTOOL_VERSION', '1.0'),
    classifiers  = [ "License :: OSI Approved :: Apache Software License" ],
    packages     = find_packages("modules"),
    package_dir  = { "": "modules" },
    package_data = { "udparsers.m2c00": [ "mex_pte.h", "mexStringFile" ] }
)
