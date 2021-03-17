"""setup.py: setuptools control."""


import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('unio/__init__.py').read(), re.M).group(1)


with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")

setup(
    name = "unio-cli",
    packages = ["unio", "lib", "resources"],
    package_data={'resources': ['*.txt', '*.key', '*.zip']},
    entry_points = {
        "console_scripts": ['unio = unio.main:main']
    },
    version = version,
    description = "cli for managing UNIO Smart Home enabled devices",
    long_description = long_descr,
    long_description_content_type='text/markdown',
    author = "UNIO Smart Home",
    author_email = "developers@freshminds.com.br",
    url = "https://github.com/uniosmarthome/unio-cli",
    python_requires='>=3.8',
    install_requires = [
        "click==7.1.2",
        "paramiko==2.7.2",
        "scp==0.13.3"
    ]
)