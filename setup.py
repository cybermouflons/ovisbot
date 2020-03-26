import os

from setuptools import setup
try:
    # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError:
    # for pip <= 9.0.3
    from pip.req import parse_requirements


def load_requirements(fname):
    reqs = parse_requirements(fname, session="test")
    return [str(ir.req) for ir in reqs]


if os.getenv("READTHEDOCS", False):
    setup(python_requires=">=3.7", install_requires=load_requirements("requirements.txt"))
else:
    setup(install_requires=load_requirements("requirements.txt"))
