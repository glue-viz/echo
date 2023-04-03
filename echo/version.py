import sys

if sys.version_info >= (3, 9):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata

__all__ = ['__version__']

__version__ = importlib_metadata.version('echo')
