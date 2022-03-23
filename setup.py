from setuptools import setup, find_packages

package_data = {
    "pel.peltool": [ "message_registry.json" ]
}

setup(
    name        = "openpower-pel-parsers",
    version     = "0.1",
    classifiers = [ "License :: OSI Approved :: Apache Software License" ],
    packages    = find_packages("modules"),
    package_dir = { "": "modules" },
    package_data    = package_data,
    scripts     = ["modules/pel/peltool/peltool.py"],
)
