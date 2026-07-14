from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent

setup(
    name="sciopy",
    version="1.0",
    packages=find_packages(),
    author="Jacob P. Thönes",
    author_email="jacob.thoenes@uni-rostock.de",
    description="Python based interface module for communication with Sciospec devices.",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    keywords="Sciospec EIT EIS".split(),
    platforms="any",
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.23",
        "pyftdi>=0.54",
        "pyserial>=3.5",
    ],
    extras_require={
        "plot": ["matplotlib>=3.6", "pyeit>=1.2"],
        "test": ["matplotlib>=3.6", "pytest>=7", "ruff>=0.11"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    url="https://github.com/EITLabworks/sciopy",
)
