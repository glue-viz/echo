from pkg_resources import get_distribution, DistributionNotFound

__all__ = ['__version__']

try:
    __version__ = get_distribution('echo').version
except DistributionNotFound:
    __version__ = 'undefined'
