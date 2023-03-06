"""
Project structure based on https://github.com/pypa/sampleproject.git
"""

from setuptools import setup, find_packages
import git


repo = git.Repo(".", search_parent_directories=True)
repo_name = repo.remotes.origin.url.split(".git")[0].split("/")[-1]

setup(
    name=repo_name,
    version="1.0",
    package_dir={"": "src/"},
    packages=find_packages(),
    author_email="romain.delabeye@gmail.com",
)
