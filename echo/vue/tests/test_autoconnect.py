import pytest

traitlets = pytest.importorskip("traitlets")

from echo import CallbackProperty, SelectionCallbackProperty, HasCallbackProperties  # noqa: E402
from echo.vue._autoconnect import autoconnect_callbacks_to_vue, _parse_template, _resolve_template  # noqa: E402


# Template uses tag-based type inference: the tag determines the handler type
# and the v-model value is the property name directly.
TEMPLATE = """
<template>
    <div>
        <v-switch v-model="x_log" />
        <v-switch v-model="y_log" />
        <v-switch v-model="show_axes" />
        <v-slider :value.sync="x_min" />
        <v-slider :value.sync="x_max" />
        <v-text-field v-model="title" />
        <v-select :items="x_att_items" v-model="x_att_selected" />
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

    # Traitlets use property names directly (no type prefix)
    assert hasattr(widget, 'x_log')
    assert hasattr(widget, 'x_min')
    assert hasattr(widget, 'title')
    assert hasattr(widget, 'x_att_items')
    assert hasattr(widget, 'x_att_selected')

    # Property NOT in template should NOT be connected
    assert 'dpi' not in handlers


def test_template_bool_bidirectional():
    state = ViewerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    assert widget.x_log is False
    assert widget.show_axes is True

    state.x_log = True
    assert widget.x_log is True

    widget.x_log = False
    assert state.x_log is False


def test_template_value_bidirectional():
    state = ViewerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    assert widget.x_min == -10.0
    state.x_min = 5.0
    assert widget.x_min == 5.0
    widget.x_max = 100.0
    assert state.x_max == 100.0


def test_template_text_bidirectional():
    state = ViewerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    assert widget.title == 'My Plot'
    state.title = 'New Title'
    assert widget.title == 'New Title'
    widget.title = 'From Widget'
    assert state.title == 'From Widget'


def test_template_choice_bidirectional():
    state = ViewerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    items = widget.x_att_items
    assert len(items) == 3
    assert items[0]['text'] == 'x'

    state.x_att = 'z'
    assert widget.x_att_selected == 2
    widget.x_att_selected = 1
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
        widget.x_log = True
        assert set_props == ['x_log']
    finally:
        state.__class__.__setattr__ = original_setattr


def test_template_warns_on_unmatched_ref():
    template = '<template><v-switch v-model="nonexistent" /></template>'
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


def test_echo_type_override():
    """echo-type attribute overrides tag-based inference."""
    template = """
    <template>
        <v-text-field v-model="x_min" echo-type="value" />
    </template>
    """
    refs = _parse_template(template)
    assert 'value' in refs
    assert 'x_min' in refs['value']
    assert 'text' not in refs


def test_text_field_number_type():
    """v-text-field with type='number' infers value."""
    template = """
    <template>
        <v-text-field type="number" v-model="age" />
    </template>
    """
    refs = _parse_template(template)
    assert 'value' in refs
    assert 'age' in refs['value']
    assert 'text' not in refs


def test_unknown_tag_warns():
    """Unknown tag without echo-type warns and skips."""
    template = '<template><glue-float-field :value.sync="x_min" /></template>'
    state = ViewerState()
    widget = SimpleWidget()
    with pytest.warns(UserWarning, match="unknown tag.*no echo-type"):
        handlers = autoconnect_callbacks_to_vue(state, widget, template=template)
    assert len(handlers) == 0


def test_unknown_tag_with_echo_type():
    """Unknown tag with echo-type works correctly."""
    template = '<template><glue-float-field :value.sync="x_min" echo-type="value" /></template>'
    state = ViewerState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(state, widget, template=template)
    assert 'x_min' in handlers
    assert widget.x_min == -10.0
    state.x_min = 42.0
    assert widget.x_min == 42.0


def test_invalid_echo_type_warns():
    """Invalid echo-type value warns and skips."""
    template = '<template><v-switch v-model="x_log" echo-type="bogus" /></template>'
    refs = _parse_template(template)
    assert len(refs) == 0


def test_resolve_template_from_template_file(tmp_path):
    """_resolve_template reads a .vue file via template_file class attribute."""
    vue_file = tmp_path / 'test.vue'
    vue_file.write_text('<template><v-switch v-model="x_log" /></template>')

    class WidgetWithTemplateFile(traitlets.HasTraits):
        template_file = (str(vue_file), 'test.vue')

    widget = WidgetWithTemplateFile()
    result = _resolve_template(widget)
    assert result == '<template><v-switch v-model="x_log" /></template>'


def test_resolve_template_from_template_traitlet():
    """_resolve_template falls back to widget.template.template."""
    class TemplateHolder:
        template = '<template><v-switch v-model="flag" /></template>'

    class WidgetWithTemplate(traitlets.HasTraits):
        pass

    widget = WidgetWithTemplate()
    widget.template = TemplateHolder()
    result = _resolve_template(widget)
    assert result == '<template><v-switch v-model="flag" /></template>'


def test_resolve_template_invalid_template_file():
    """_resolve_template skips template_file that isn't a valid tuple."""
    class WidgetWithBadTemplateFile(traitlets.HasTraits):
        template_file = 'not-a-tuple'

    widget = WidgetWithBadTemplateFile()
    assert _resolve_template(widget) is None


def test_resolve_template_returns_none():
    """_resolve_template returns None when no template is found."""
    widget = SimpleWidget()
    assert _resolve_template(widget) is None


def test_extras_connect():
    """extras dict connects properties not in the template."""
    template = '<template><v-switch v-model="x_log" /></template>'
    state = ViewerState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(
        state, widget, template=template,
        extras={'show_axes': 'bool', 'x_min': 'value', 'title': 'text'},
    )
    assert 'x_log' in handlers
    assert 'show_axes' in handlers
    assert 'x_min' in handlers
    assert 'title' in handlers

    # Verify bidirectional sync works for extras
    state.show_axes = False
    assert widget.show_axes is False
    widget.x_min = 99.0
    assert state.x_min == 99.0


def test_extras_invalid_type_warns():
    """extras with an invalid type warns and skips."""
    template = '<template></template>'
    state = ViewerState()
    widget = SimpleWidget()
    with pytest.warns(UserWarning, match="Unknown type 'bogus'"):
        handlers = autoconnect_callbacks_to_vue(
            state, widget, template=template,
            extras={'x_log': 'bogus'},
        )
    assert len(handlers) == 0


def test_extras_missing_property_warns():
    """extras referencing a non-existent property warns and skips."""
    template = '<template></template>'
    state = ViewerState()
    widget = SimpleWidget()
    with pytest.warns(UserWarning, match="not a callback property"):
        handlers = autoconnect_callbacks_to_vue(
            state, widget, template=template,
            extras={'nonexistent': 'bool'},
        )
    assert len(handlers) == 0


def test_extras_choice():
    """extras can connect SelectionCallbackProperty via combosel."""
    template = '<template></template>'
    state = ViewerState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(
        state, widget, template=template,
        extras={'x_att': 'combosel'},
    )
    assert 'x_att' in handlers
    assert hasattr(widget, 'x_att_items')
    assert hasattr(widget, 'x_att_selected')
    assert len(widget.x_att_items) == 3


def test_extras_with_transforms():
    """extras tuple form applies custom transforms."""
    template = '<template></template>'
    state = ViewerState()
    widget = SimpleWidget()
    connections = autoconnect_callbacks_to_vue(
        state, widget, template=template,
        extras={'x_min': ('text', lambda v: f'val={v}', lambda s: float(s.split('=')[1]))},
    )
    assert 'x_min' in connections
    # to_widget transform applied
    assert widget.x_min == 'val=-10.0'
    # State change goes through to_widget
    state.x_min = 5.0
    assert widget.x_min == 'val=5.0'
    # Widget change goes through from_widget
    widget.x_min = 'val=42.0'
    assert state.x_min == 42.0


def test_extras_override_template_type():
    """extras override the template-inferred type for the same property."""
    # Template infers x_min as 'value' from v-slider, but extras override to 'text'
    template = '<template><v-slider :value.sync="x_min" /></template>'
    state = ViewerState()
    widget = SimpleWidget()
    connections = autoconnect_callbacks_to_vue(
        state, widget, template=template,
        extras={'x_min': ('text', str, float)},
    )
    assert 'x_min' in connections
    # Should be a text traitlet (from extras), not a float (from template)
    assert widget.x_min == '-10.0'


def test_only_skips_template():
    """only connects listed properties without parsing a template."""
    state = ViewerState()
    widget = SimpleWidget()
    connections = autoconnect_callbacks_to_vue(
        state, widget,
        only={'x_log': 'bool', 'x_min': 'value'},
    )
    assert set(connections) == {'x_log', 'x_min'}
    # Not in only → not connected
    assert not hasattr(widget, 'title')

    state.x_log = True
    assert widget.x_log is True
    widget.x_min = 99.0
    assert state.x_min == 99.0


def test_only_with_transforms():
    """only supports transform tuples."""
    state = ViewerState()
    widget = SimpleWidget()
    connections = autoconnect_callbacks_to_vue(
        state, widget,
        only={'x_min': ('text', str, float)},
    )
    assert widget.x_min == '-10.0'
    widget.x_min = '7.5'
    assert state.x_min == 7.5
