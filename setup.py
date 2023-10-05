from setuptools import setup, find_packages
import os

setup(
    name         = "openpower-pel-parsers",
    version      = os.getenv('PELTOOL_VERSION', '1.0'),
    classifiers  = [ "License :: OSI Approved :: Apache Software License" ],
    packages     = find_packages("modules"),
    package_dir  = { "": "modules" },
    package_data = { "io_drawer": [ "mex_pte.h", "nimitz_pte.h",
                                    "mexStringFile", "nimitzStringFile" ] }
)
