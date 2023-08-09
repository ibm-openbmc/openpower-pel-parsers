from setuptools import setup
import os

# This package is just used to install all of the component peltool
# packages and doesn't contain any code of its own.

version = os.getenv('PELTOOL_VERSION', '0.2')

setup(
    name        = "peltool-wrapper",
    version     = f'{version}',
    classifiers = [ "License :: OSI Approved :: Apache Software License" ],
    packages = ['peltool-wrapper'],
    install_requires = [
        f"openpower-pel-parsers >= {version}",
        f"Hostboot >= {version}",
        f"sbe-pel-parser >= {version}",
        f"pel-message-registry >= {version}",
        f"openpower-hw-diags-pel-parser-data >= {version}",
        f"occ-pel-parser >= {version}"
        ]
)
