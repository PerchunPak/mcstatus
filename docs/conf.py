"""Configuration file for the Sphinx documentation builder.

This file does only contain a selection of the most common options. For a
full list see the documentation:
http://www.sphinx-doc.org/en/master/config
"""

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

from __future__ import annotations

import os
import sys
from datetime import date
from typing import TYPE_CHECKING

from packaging.version import parse as parse_version

# Since pyright assumes lowest supported version, it would default to using tomli
# which we don't want, as it's only installed if on <3.11 and pyright usually runs
# on latest versions. For that reason, we include or TYPE_CHECKING in the condition.
if sys.version_info >= (3, 11) or TYPE_CHECKING:
    from tomllib import load as toml_parse
else:
    from tomli import load as toml_parse

sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------


def _get_project_meta() -> dict[str, str]:
    with open("../pyproject.toml", "rb") as pyproject:
        return toml_parse(pyproject)["project"]  # type: ignore[no-any-return]


pkg_meta = _get_project_meta()
project = str(pkg_meta["name"])
copyright = str(date.today().year) + ", py-mine"
author = "Dinnerbone"

parsed_version = parse_version(pkg_meta["version"])

# The short X.Y version
version = parsed_version.base_version
# The full version, including alpha/beta/rc tags
release = str(parsed_version)


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named "sphinx.ext.*") or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    # Used to reference for third party projects:
    "sphinx.ext.intersphinx",
    # Used to include .md files:
    "m2r2",
]

autoclass_content = "both"
autodoc_member_order = "bysource"

autodoc_default_flags = {
    "members": "",
    "undoc-members": "code,error_template",
    "exclude-members": "__dict__,__weakref__",
}

# Automatically generate section labels:
autosectionlabel_prefix_document = True

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:

source_suffix = [".rst", ".md"]

# The master toctree document.
master_doc = "index"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

add_module_names = False

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "furo"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "navigation_with_keys": True,
}

# -- Extension configuration -------------------------------------------------

# Third-party projects documentation references:
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "dns": ("https://dnspython.readthedocs.io/en/stable/", None),
}


# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


# Mocks
def mock_autodoc() -> None:
    """Mock autodoc to not add ``Bases: object`` to the classes, that do not have super classes.

    See also https://stackoverflow.com/a/75041544/20952782.
    """
    from sphinx.ext import autodoc

    class MockedClassDocumenter(autodoc.ClassDocumenter):
        def add_line(self, line: str, source: str, *lineno: int) -> None:
            if line == "   Bases: :py:class:`object`":
                return
            super().add_line(line, source, *lineno)

    autodoc.ClassDocumenter = MockedClassDocumenter


def delete_doc_for_address_base() -> None:
    """``__new__`` is appended to the docstring of ``AddressBase``.

    And we do not want autogenerated nonsense docstring there.
    """
    from mcstatus.address import _AddressBase

    del _AddressBase.__new__.__doc__


mock_autodoc()
delete_doc_for_address_base()
