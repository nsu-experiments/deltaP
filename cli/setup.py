#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for ΔP interpreter and package manager.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README if it exists
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="deltap",
    version="0.1.0",
    author="Janne",
    author_email="ruponez@gmail.com",
    description="The ΔP Programming Language: Combining Imperative, Logical, and Probabilistic Capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nsu-experiments/deltaP",
    license="MIT",
    packages=find_packages(include=["interpreter", "interpreter.*", "cli", "cli.*"]),
    python_requires=">=3.11",
    install_requires=[
        "ply>=3.11",
        "h5py>=3.8.0",
        "numpy>=1.24.0",
        "tomli>=2.0.0; python_version<'3.11'",  # tomllib is built-in for 3.11+
    ],
    entry_points={
        "console_scripts": [
            "dp=cli:main",  # Creates 'dp' command
            "deltap=interpreter.__main__:main",  # Alternative: 'deltap' command for interpreter
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    include_package_data=True,
    zip_safe=False,
)