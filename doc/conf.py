from echo import __version__

project = "echo"
copyright = "2014-2020, Chris Beaumont and Thomas Robitaille"
version = release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_automodapi.automodapi",
    "sphinx_automodapi.smart_resolver",
    "numpydoc",
]

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
exclude_patterns = ["_build"]
pygments_style = "sphinx"

nitpicky = True
nitpick_ignore = [
    ("py:class", "echo.containers.ContainerMixin"),
    ("py:class", "None.  Remove all items from D."),
    ("py:class", "a shallow copy of D"),
    ("py:class", "a set-like object providing a view on D's items"),
    ("py:class", "a set-like object providing a view on D's keys"),
    ("py:class", "v, remove specified key and return the corresponding value."),
    ("py:class", "None.  Update D from dict/iterable E and F."),
    ("py:class", "None.  Update D from mapping/iterable E and F."),
    ("py:class", "an object providing a view on D's values"),
]

numpydoc_class_members_toctree = False

intersphinx_cache_limit = 10
intersphinx_mapping = {
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
    "python": ("https://docs.python.org/3.6", None),
}
