# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import sys
import os
import shutil

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))

from openquake import engine

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "OpenQuake Engine"
copyright = "2023, GEM Foundation"
author = "GEM Foundation"
release = "v1.0.0"

try:
    import subprocess
    import re
    vcs_branch = subprocess.run(['git', 'branch', '--show-current'], stdout=subprocess.PIPE)
    vcs_branch = vcs_branch.stdout.decode('utf-8').rstrip()
    it_is_master = False
    if vcs_branch == 'master' or vcs_branch == 'vers-adv-man2':
        it_is_master = True

    # vcs_branch = 'engine-3.15'
    if re.compile('engine-[0-9]+\.[0-9]+.*').match(vcs_branch):
        branch = ''
    else:
        branch = " (%s)" % vcs_branch
except Exception:
    vcs_branch = None
    branch = ''

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y.Z version.
version = engine.__version__.split('-')[0]
# The full version, including alpha/beta/rc tags.

if it_is_master:
    release = "devel. (%s)" % (engine.__version__,)
else:
    release = "%s%s" % (engine.__version__, branch)


rst_epilog = """
.. |VERSION| replace:: %s
""" % release

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_favicon = "_static/OQ-Logo circle_shade.png"


json_url_path = ".ddown_doc23.json"
if not os.path.exists(json_url_path):
    shutil.copyfile("samples/dot_ddown_doc23.json.sample",
                    json_url_path)

it_is_master = False

html_theme_options = {
    "navigation_with_keys": True,
    "show_nav_level": 2,
    "content_footer_items": ["last-updated"],
    "header_links_before_dropdown": 6,
    "navbar_start": ["navbar-logo", "version-switcher"],
    "switcher": {
        "json_url": json_url_path,
#        "version_match": "development" if it_is_master is True else '.'.join(version.split('.')[0:2])
         "version_match": "master"
    },
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
