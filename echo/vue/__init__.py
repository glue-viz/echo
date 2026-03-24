try:
    from .autoconnect import autoconnect_callbacks_to_vue  # noqa
except ImportError:  # pragma: no cover
    pass

__all__ = ['autoconnect_callbacks_to_vue']
