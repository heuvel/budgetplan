from setuptools import setup, find_packages

base_packages = []

test_packages = ["pytest>=6.2.2", "black>=20.8b1", "flake8>=3.9.0"]

util_packages = ["jupyterlab>=2.2.6"]

dev_packages = test_packages + util_packages


setup(
    name="budgetplan",
    version="0.1.0",
    packages=find_packages(),
    extras_requires={"dev": dev_packages, "test": test_packages},
)
