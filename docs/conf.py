import os
import sys
from datetime import datetime

# Allow importing the package from repo root
sys.path.insert(0, os.path.abspath(".."))

project = "sciopy"
author = "Jacob P. Thönes"
release = "0.8.2.2"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx.ext.intersphinx",
    "nbsphinx",
]

autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Project logo shown in the theme header
html_logo = "_static/logo_sciopy.jpg"

# Intersphinx mapping to useful external docs
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

# Linkcheck settings (tolerate some known external issues)
linkcheck_ignore = [r"https://localhost:\d+/"]
linkcheck_timeout = 10

# Small helper for copyright line
copyright = f"{datetime.now().year}, {author}"

# Mock imports if building on CI without installing heavy deps (adjust as needed)
autodoc_mock_imports = [
    "numpy",
    "pandas",
    "matplotlib",
    "serial",
    "pyeit",
    "pyftdi",
    "pyserial",
    "tqdm",
]
