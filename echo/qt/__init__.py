try:
    import pytest
    pytest.importorskip('qtpy')
except ImportError:
    pass

from .connect import *   # noqa
from .autoconnect import *  # noqa
