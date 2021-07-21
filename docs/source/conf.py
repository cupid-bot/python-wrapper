"""Configuration file for the Sphinx documentation builder.

For options, see https://www.sphinx-doc.org/en/master/usage/configuration.html.
"""
import pathlib
import sys


sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

project = 'Python Cupid'
copyright = '2021, Artemis'
author = 'Artemis'
release = '0.4.3'

extensions = ['sphinx.ext.autodoc']
templates_path = ['templates']
html_theme = 'furo'
html_static_path = ['static']
html_logo = 'static/logo.png'
html_css_files = ['style.css']
