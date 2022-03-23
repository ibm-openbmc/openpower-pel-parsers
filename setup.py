from setuptools import setup, find_packages

setup(
    name        = "openpower-pel-parsers",
    version     = "1.0",
    classifiers = [ "License :: OSI Approved :: Apache Software License" ],
    packages    = find_packages("modules"),
    package_dir = { "": "modules" }
)
