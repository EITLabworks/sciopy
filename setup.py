from setuptools import setup, find_packages

setup(
    name="sciopy",
    version="0.8.9",
    packages=find_packages(),
    author="Jacob P. Thönes",
    author_email="jacob.thoenes@uni-rostock.de",
    description="Python based interface module for communication with the Sciospec Electrical Impedance Tomography (EIT) device.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="Sciospec EIT EIS".split(),
    platforms="any",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    url="https://github.com/spatialaudio/sciopy.git",
)
