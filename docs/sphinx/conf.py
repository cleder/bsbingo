"""
Sphinx configuration for the Bullshit Bingo backend documentation.

Minimal MyST-based scaffold satisfying constitution Principle III
(Documentation First: docs kept in Sphinx) for this feature's own
documentation, without migrating the repo's existing mkdocs-material
docs tree.
"""

project = "Bullshit Bingo"
extensions = ["myst_parser"]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
master_doc = "index"
exclude_patterns = ["_build"]
html_theme = "alabaster"
