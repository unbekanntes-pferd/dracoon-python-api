import os
import io
from setuptools import setup, find_packages

# The directory containing this file
DESCRIPTION = "DRACOON API wrapper in Python"
here = os.path.abspath(os.path.dirname(__file__))

# The text of the README file
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        README = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# This call to setup() does all the work
setup(
    name="dracoon",
    version="1.8.3",
    description=DESCRIPTION,
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/unbekanntes-pferd/DRACOON-PYTHON-API",
    author="Octavio Simone",
    author_email="octsim@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=["httpx", "asyncio", "pydantic", "cryptography", "tqdm"]
)