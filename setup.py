import os

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'README.md')) as f:
    README = f.read()

setup(
    name='checkmate',
    version='3.0',
    description='Hypothesis Checkmate Service',
    long_description=README,
    url='https://github.com/hypothesis/checkmate',
    packages=find_packages(),
    include_package_data=True,
    entry_points="""\
    [console_scripts]
    devdata = checkmate.scripts:update_dev_data
    initdb = checkmate.scripts:initialize_db
    """,
)
