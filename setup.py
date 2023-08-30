"""
Project structure based on https://github.com/pypa/sampleproject.git
"""

from setuptools import setup, find_packages


repo_name = "wonka"

setup(
    name=repo_name,
    version="1.0",
    package_dir={"": "src/"},
    packages=find_packages(),
    author_email="romain.delabeye@gmail.com",
)
