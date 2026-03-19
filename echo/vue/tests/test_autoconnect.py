import pytest

traitlets = pytest.importorskip("traitlets")

from echo import CallbackProperty, SelectionCallbackProperty, HasCallbackProperties  # noqa: E402
from echo.vue.autoconnect import autoconnect_callbacks_to_vue, _parse_template  # noqa: E402


# Template uses {type}_{name} convention to declare handler types.
TEMPLATE = """
<template>
    <div>
        <v-switch v-model="bool_x_log" />
        <v-switch v-model="bool_y_log" />
        <v-switch v-model="bool_show_axes" />
        <glue-float-field :value.sync="value_x_min" />
        <glue-float-field :value.sync="value_x_max" />
        <v-text-field v-model="text_title" />
        <v-select :items="combosel_x_att_items" v-model="combosel_x_att_selected" />
    </div>
</template>
"""


class ViewerState(HasCallbackProperties):
    x_log = CallbackProperty(False)
    y_log = CallbackProperty(False)
    show_axes = CallbackProperty(True)
    x_min = CallbackProperty(-10.0)
    x_max = CallbackProperty(30.0)
    title = CallbackProperty('My Plot')
    x_att = SelectionCallbackProperty(default_index=0)
    # Property NOT in the template:
    dpi = CallbackProperty(72)

    def __init__(self):
        super().__init__()
        ViewerState.x_att.set_choices(self, ['x', 'y', 'z'])


class SimpleWidget(traitlets.HasTraits):
    pass


# --- Template mode tests ---

def test_parse_template():
    refs = _parse_template(TEMPLATE)
    assert refs['bool'] == {'x_log', 'y_log', 'show_axes'}
    assert refs['value'] == {'x_min', 'x_max'}
    assert refs['text'] == {'title'}
    assert refs['combosel'] == {'x_att'}


def test_template_creates_only_referenced_traits():
    state = ViewerState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    # Properties referenced in template should be connected
    assert 'x_log' in handlers
    assert 'show_axes' in handlers
    assert 'x_min' in handlers
    assert 'title' in handlers
    assert 'x_att' in handlers

    # Traitlets use {type}_{name} naming
    assert hasattr(widget, 'bool_x_log')
    assert hasattr(widget, 'value_x_min')
    assert hasattr(widget, 'text_title')
    assert hasattr(widget, 'combosel_x_att_items')
    assert hasattr(widget, 'combosel_x_att_selected')

    # Property NOT in template should NOT be connected
    assert 'dpi' not in handlers


def test_template_bool_bidirectional():
    state = ViewerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    assert widget.bool_x_log is False
    assert widget.bool_show_axes is True

    state.x_log = True
    assert widget.bool_x_log is True

    widget.bool_x_log = False
    assert state.x_log is False


def test_template_value_bidirectional():
    state = ViewerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    assert widget.value_x_min == -10.0
    state.x_min = 5.0
    assert widget.value_x_min == 5.0
    widget.value_x_max = 100.0
    assert state.x_max == 100.0


def test_template_text_bidirectional():
    state = ViewerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    assert widget.text_title == 'My Plot'
    state.title = 'New Title'
    assert widget.text_title == 'New Title'
    widget.text_title = 'From Widget'
    assert state.title == 'From Widget'


def test_template_choice_bidirectional():
    state = ViewerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    items = widget.combosel_x_att_items
    assert len(items) == 3
    assert items[0]['text'] == 'x'

    state.x_att = 'z'
    assert widget.combosel_x_att_selected == 2
    widget.combosel_x_att_selected = 1
    assert state.x_att == 'y'


def test_template_atomic_no_stale_overwrite():
    """Setting a bool via the widget only syncs that one property."""
    state = ViewerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    set_props = []
    original_setattr = state.__class__.__setattr__

    def tracking_setattr(self, name, value):
        if not name.startswith('_'):
            set_props.append(name)
        original_setattr(self, name, value)

    state.__class__.__setattr__ = tracking_setattr
    try:
        set_props.clear()
        widget.bool_x_log = True
        assert set_props == ['x_log']
    finally:
        state.__class__.__setattr__ = original_setattr


def test_template_warns_on_unmatched_ref():
    template = '<template><v-switch v-model="bool_nonexistent" /></template>'
    state = ViewerState()
    widget = SimpleWidget()
    with pytest.warns(UserWarning, match="'nonexistent' is not a callback property"):
        autoconnect_callbacks_to_vue(state, widget, template=template)


def test_template_empty():
    state = ViewerState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(state, widget, template='<template></template>')
    assert len(handlers) == 0


def test_no_template_raises():
    state = ViewerState()
    widget = SimpleWidget()
    with pytest.raises(ValueError, match="No Vue template found"):
        autoconnect_callbacks_to_vue(state, widget)
