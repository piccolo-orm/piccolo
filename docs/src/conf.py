# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import datetime
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------

year = datetime.datetime.now().strftime("%Y")
project = "Piccolo"
author = "Daniel Townsend"
copyright = f"{year}, {author}"


import piccolo  # noqa: E402

version = ".".join(piccolo.__VERSION__.split(".")[:2])
release = piccolo.__VERSION__

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.coverage",
]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# -- Intersphinx -------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "piccolo_api": ("https://piccolo-api.readthedocs.io/en/latest/", None),
}
extensions += ["sphinx.ext.intersphinx"]

# -- Autodoc -----------------------------------------------------------------

extensions += ["sphinx.ext.autodoc"]
autodoc_typehints = "signature"
autodoc_typehints_format = "short"
autoclass_content = "both"

# -- Options for HTML output -------------------------------------------------

html_theme = "piccolo_theme"
html_short_title = "Piccolo"
html_show_sphinx = False
globaltoc_maxdepth = 3
html_theme_options = {
    "source_url": "https://github.com/piccolo-orm/piccolo/",
}

# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "Piccolodoc"

# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(master_doc, "piccolo", "Piccolo Documentation", [author], 1)]
