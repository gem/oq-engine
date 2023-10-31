# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import sys
import os

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "OpenQuake Engine"
copyright = "2023, GEM Foundation"
author = "GEM Foundation"
release = "v1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_favicon = "_static/OQ-Logo circle_shade.png"
html_theme_options = {
    "navigation_with_keys": True,
    "show_nav_level": 2,
    "content_footer_items": ["last-updated"],
    "header_links_before_dropdown": 6,
    "navbar_start": ["navbar-logo"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
    "navbar_persistent": ["search-button"],
    "logo": {
        "image_light": "_static/OQ-Logo-Standard-RGB-72DPI-01-transparent.png",
        "image_dark": "_static/OQ-Logo-Inverted-RGB-72DPI-01.jpg",
    },
    "icon_links": [
        {
            "name": "GEM",
            "url": "https://www.globalquakemodel.org",
            "icon": "_static/GEM-LOGO-Plain-RGB-72DPI-01.png",
            "type": "local",
        },
        {
            "name": "GitHub",
            "url": "https://github.com/gem/oq-engine",
            "icon": "fa-brands fa-square-github",
            "type": "fontawesome",
        },
        {
            "name": "Linkedin",
            "url": "https://linkedin.com/company/gem-foundation",
            "icon": "fa-brands fa-linkedin",
            "type": "fontawesome",
        },
        {
            "name": "X/Twitter",
            "url": "https://x.com/GEMwrld",
            "icon": "fa-brands fa-square-twitter",
            "type": "fontawesome",
        },
        {
            "name": "YouTube",
            "url": "https://youtube.com/@gemglobalearthquakemodel3652",
            "icon": "fa-brands fa-square-youtube",
            "type": "fontawesome",
        },
        {
            "name": "Facebook",
            "url": "https://fb.com/GEMwrld/",
            "icon": "fa-brands fa-square-facebook",
            "type": "fontawesome",
        },
    ],
}
html_context = {"default_mode": "light"}
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx.ext.autosectionlabel",
    "sphinxcontrib.images",
    "sphinxcontrib.youtube",
]
