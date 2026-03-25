import logging

import pytest

traitlets = pytest.importorskip("traitlets")

from echo import CallbackProperty, HasCallbackProperties  # noqa: E402
from echo.vue._autoconnect import autoconnect_callbacks_to_vue  # noqa: E402
from echo.vue._log import enable_comm_logging, disable_comm_logging  # noqa: E402

TEMPLATE = """
<template>
    <v-slider :value.sync="x_min" />
</template>
"""


class State(HasCallbackProperties):
    x_min = CallbackProperty(0.0)


class Widget(traitlets.HasTraits):
    """Minimal stand-in for an ipywidget that calls _send on trait changes."""

    def _send(self, msg, buffers=None):
        pass

    def set_state(self, sync_data):
        for k, v in sync_data.items():
            setattr(self, k, v)

    def _notify_trait(self, name, old_value, new_value):
        super()._notify_trait(name, old_value, new_value)
        trait = self.traits().get(name)
        if trait and trait.metadata.get('sync'):
            self._send({'method': 'update', 'state': {name: new_value}})


@pytest.fixture(autouse=True)
def _clean_logging_state():
    disable_comm_logging()
    yield
    disable_comm_logging()


@pytest.fixture
def connected_pair():
    state = State()
    widget = Widget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)
    return state, widget


@pytest.fixture
def logged_pair():
    enable_comm_logging()
    state = State()
    widget = Widget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)
    return state, widget


def test_logging_captures_state_to_widget(caplog, logged_pair):
    state, widget = logged_pair
    with caplog.at_level(logging.DEBUG, logger='echo'):
        state.x_min = 5.0
    assert any('[PY->VUE]' in r.message for r in caplog.records)


def test_logging_captures_widget_to_state(caplog, logged_pair):
    state, widget = logged_pair
    with caplog.at_level(logging.DEBUG, logger='echo'):
        widget.set_state({'x_min': 3.0})
    assert any('[VUE->PY]' in r.message for r in caplog.records)


def test_no_logging_when_disabled(caplog, connected_pair):
    state, widget = connected_pair
    with caplog.at_level(logging.DEBUG, logger='echo'):
        state.x_min = 5.0
        widget.set_state({'x_min': 3.0})
    assert not any('[PY->VUE]' in r.message or '[VUE->PY]' in r.message
                   for r in caplog.records)


def test_disable_stops_logging(caplog, logged_pair):
    state, widget = logged_pair
    disable_comm_logging()
    with caplog.at_level(logging.DEBUG, logger='echo'):
        state.x_min = 5.0
        widget.set_state({'x_min': 3.0})
    assert not any('[PY->VUE]' in r.message or '[VUE->PY]' in r.message
                   for r in caplog.records)
