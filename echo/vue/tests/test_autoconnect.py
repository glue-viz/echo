import warnings

import pytest

traitlets = pytest.importorskip("traitlets")

from echo import (  # noqa: E402  # noqa: E402
    CallbackProperty,
    DictCallbackProperty,
    HasCallbackProperties,
    ListCallbackProperty,
    SelectionCallbackProperty,
)
from echo.vue._autoconnect import _parse_template, _resolve_template, autoconnect_callbacks_to_vue  # noqa: E402

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
    title = CallbackProperty("My Plot")
    x_att = SelectionCallbackProperty(default_index=0)
    # Property NOT in the template:
    dpi = CallbackProperty(72)

    def __init__(self):
        super().__init__()
        ViewerState.x_att.set_choices(self, ["x", "y", "z"])


class SimpleWidget(traitlets.HasTraits):
    pass


# --- Template mode tests ---


def test_parse_template():
    refs = _parse_template(TEMPLATE)
    assert refs["bool"] == {"x_log", "y_log", "show_axes"}
    assert refs["float"] == {"x_min", "x_max"}
    assert refs["text"] == {"title"}
    assert refs["selection"] == {"x_att"}


def test_template_creates_only_referenced_traits():
    state = ViewerState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    # Properties referenced in template should be connected
    assert "x_log" in handlers
    assert "show_axes" in handlers
    assert "x_min" in handlers
    assert "title" in handlers
    assert "x_att" in handlers

    # Traitlets use property names directly (no type prefix)
    assert hasattr(widget, "x_log")
    assert hasattr(widget, "x_min")
    assert hasattr(widget, "title")
    assert hasattr(widget, "x_att_items")
    assert hasattr(widget, "x_att_selected")

    # Property NOT in template should NOT be connected
    assert "dpi" not in handlers


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

    assert widget.title == "My Plot"
    state.title = "New Title"
    assert widget.title == "New Title"
    widget.title = "From Widget"
    assert state.title == "From Widget"


def test_template_choice_bidirectional():
    state = ViewerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    items = widget.x_att_items
    assert len(items) == 3
    assert items[0]["text"] == "x"

    state.x_att = "z"
    assert widget.x_att_selected == 2
    widget.x_att_selected = 1
    assert state.x_att == "y"


def test_template_atomic_no_stale_overwrite():
    """Setting a bool via the widget only syncs that one property."""
    state = ViewerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, template=TEMPLATE)

    set_props = []
    original_setattr = state.__class__.__setattr__

    def tracking_setattr(self, name, value):
        if not name.startswith("_"):
            set_props.append(name)
        original_setattr(self, name, value)

    state.__class__.__setattr__ = tracking_setattr
    try:
        set_props.clear()
        widget.x_log = True
        assert set_props == ["x_log"]
    finally:
        state.__class__.__setattr__ = original_setattr


def test_template_warns_on_unmatched_ref():
    template = '<template><v-switch v-model="nonexistent" /></template>'
    state = ViewerState()
    widget = SimpleWidget()
    with pytest.warns(UserWarning, match="'nonexistent' is not a callback property"):
        autoconnect_callbacks_to_vue(state, widget, template=template)


def test_no_warning_when_widget_has_trait():
    """No warning when template references a trait that exists on the widget but not on the state."""
    template = '<template><v-text-field v-model="custom_txt" /><v-switch v-model="x_log" /></template>'
    state = ViewerState()

    class WidgetWithTrait(traitlets.HasTraits):
        custom_txt = traitlets.Unicode("hello").tag(sync=True)

    widget = WidgetWithTrait()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        handlers = autoconnect_callbacks_to_vue(state, widget, template=template)
    # custom_txt should be skipped (not connected), x_log should be connected
    assert "custom_txt" not in handlers
    assert "x_log" in handlers


def test_template_empty():
    state = ViewerState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(state, widget, template="<template></template>")
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
        <v-text-field v-model="x_min" echo-type="float" />
    </template>
    """
    refs = _parse_template(template)
    assert "float" in refs
    assert "x_min" in refs["float"]
    assert "text" not in refs


def test_text_field_number_type():
    """v-text-field with type='number' infers int."""
    template = """
    <template>
        <v-text-field type="number" v-model="age" />
    </template>
    """
    refs = _parse_template(template)
    assert "int" in refs
    assert "age" in refs["int"]
    assert "text" not in refs


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
    template = '<template><glue-float-field :value.sync="x_min" echo-type="float" /></template>'
    state = ViewerState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(state, widget, template=template)
    assert "x_min" in handlers
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
    vue_file = tmp_path / "test.vue"
    vue_file.write_text('<template><v-switch v-model="x_log" /></template>')

    class WidgetWithTemplateFile(traitlets.HasTraits):
        template_file = (str(vue_file), "test.vue")

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
        template_file = "not-a-tuple"

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
        state,
        widget,
        template=template,
        extras={"show_axes": "bool", "x_min": "float", "title": "text"},
    )
    assert "x_log" in handlers
    assert "show_axes" in handlers
    assert "x_min" in handlers
    assert "title" in handlers

    # Verify bidirectional sync works for extras
    state.show_axes = False
    assert widget.show_axes is False
    widget.x_min = 99.0
    assert state.x_min == 99.0


def test_extras_invalid_type_warns():
    """extras with an invalid type warns and skips."""
    template = "<template></template>"
    state = ViewerState()
    widget = SimpleWidget()
    with pytest.warns(UserWarning, match="Unknown type 'bogus'"):
        handlers = autoconnect_callbacks_to_vue(
            state,
            widget,
            template=template,
            extras={"x_log": "bogus"},
        )
    assert len(handlers) == 0


def test_extras_missing_property_warns():
    """extras referencing a non-existent property warns and skips."""
    template = "<template></template>"
    state = ViewerState()
    widget = SimpleWidget()
    with pytest.warns(UserWarning, match="not a callback property"):
        handlers = autoconnect_callbacks_to_vue(
            state,
            widget,
            template=template,
            extras={"nonexistent": "bool"},
        )
    assert len(handlers) == 0


def test_extras_choice():
    """extras can connect SelectionCallbackProperty via selection."""
    template = "<template></template>"
    state = ViewerState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(
        state,
        widget,
        template=template,
        extras={"x_att": "selection"},
    )
    assert "x_att" in handlers
    assert hasattr(widget, "x_att_items")
    assert hasattr(widget, "x_att_selected")
    assert len(widget.x_att_items) == 3


def test_extras_with_transforms():
    """extras tuple form applies custom transforms."""
    template = "<template></template>"
    state = ViewerState()
    widget = SimpleWidget()
    connections = autoconnect_callbacks_to_vue(
        state,
        widget,
        template=template,
        extras={"x_min": ("text", lambda v: f"val={v}", lambda s: float(s.split("=")[1]))},
    )
    assert "x_min" in connections
    # to_widget transform applied
    assert widget.x_min == "val=-10.0"
    # State change goes through to_widget
    state.x_min = 5.0
    assert widget.x_min == "val=5.0"
    # Widget change goes through from_widget
    widget.x_min = "val=42.0"
    assert state.x_min == 42.0


def test_extras_override_template_type():
    """extras override the template-inferred type for the same property."""
    # Template infers x_min as 'float' from v-slider, but extras override to 'text'
    template = '<template><v-slider :value.sync="x_min" /></template>'
    state = ViewerState()
    widget = SimpleWidget()
    connections = autoconnect_callbacks_to_vue(
        state,
        widget,
        template=template,
        extras={"x_min": ("text", str, float)},
    )
    assert "x_min" in connections
    # Should be a text traitlet (from extras), not a float (from template)
    assert widget.x_min == "-10.0"


def test_skip():
    """skip prevents listed properties from being connected or warned about."""
    state = ViewerState()
    widget = SimpleWidget()
    connections = autoconnect_callbacks_to_vue(
        state,
        widget,
        template=TEMPLATE,
        skip={"x_min", "title"},
    )
    assert "x_min" not in connections
    assert "title" not in connections
    assert "x_log" in connections
    assert not hasattr(widget, "x_min")
    assert not hasattr(widget, "title")


def test_only_skips_template():
    """only connects listed properties without parsing a template."""
    state = ViewerState()
    widget = SimpleWidget()
    connections = autoconnect_callbacks_to_vue(
        state,
        widget,
        only={"x_log": "bool", "x_min": "float"},
    )
    assert set(connections) == {"x_log", "x_min"}
    # Not in only → not connected
    assert not hasattr(widget, "title")

    state.x_log = True
    assert widget.x_log is True
    widget.x_min = 99.0
    assert state.x_min == 99.0


def test_only_with_transforms():
    """only supports transform tuples."""
    state = ViewerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(
        state,
        widget,
        only={"x_min": ("text", str, float)},
    )
    assert widget.x_min == "-10.0"
    widget.x_min = "7.5"
    assert state.x_min == 7.5


# --- List and Dict connection tests ---


class ContainerState(HasCallbackProperties):
    items = ListCallbackProperty([{"name": "a"}, {"name": "b"}])
    settings = DictCallbackProperty({"visible": True, "nested": {"x": 1, "y": 2}})
    tags = ListCallbackProperty(["red", "green"])


def test_list_state_to_widget():
    state = ContainerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"items": "list"})
    assert widget.items == [{"name": "a"}, {"name": "b"}]


def test_list_state_mutation_syncs():
    state = ContainerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"items": "list"})
    state.items.append({"name": "c"})
    assert len(widget.items) == 3
    assert widget.items[2] == {"name": "c"}


def test_list_widget_to_state():
    state = ContainerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"items": "list"})
    widget.items = [{"name": "x"}]
    assert len(state.items) == 1
    assert state.items[0] == {"name": "x"}


def test_list_widget_updates_in_place():
    """Widget changes update the existing CallbackList rather than replacing it."""
    state = ContainerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"items": "list"})
    original_list = state.items
    widget.items = [{"name": "x"}, {"name": "y"}]
    assert state.items is original_list


def test_list_simple_values():
    state = ContainerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"tags": "list"})
    assert widget.tags == ["red", "green"]
    state.tags.append("blue")
    assert widget.tags == ["red", "green", "blue"]
    widget.tags = ["one"]
    assert list(state.tags) == ["one"]


def test_dict_state_to_widget():
    state = ContainerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"settings": "dict"})
    assert widget.settings == {"visible": True, "nested": {"x": 1, "y": 2}}


def test_dict_state_mutation_syncs():
    state = ContainerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"settings": "dict"})
    state.settings["visible"] = False
    assert widget.settings["visible"] is False


def test_dict_nested_mutation_syncs():
    state = ContainerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"settings": "dict"})
    state.settings["nested"]["x"] = 99
    assert widget.settings["nested"]["x"] == 99


def test_dict_widget_to_state():
    state = ContainerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"settings": "dict"})
    widget.settings = {"visible": False, "nested": {"x": 5, "y": 6}}
    assert state.settings["visible"] is False
    assert state.settings["nested"]["x"] == 5


def test_dict_widget_updates_in_place():
    """Widget changes update the existing CallbackDict rather than replacing it."""
    state = ContainerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"settings": "dict"})
    original_dict = state.settings
    original_nested = state.settings["nested"]
    widget.settings = {"visible": False, "nested": {"x": 5, "y": 6}}
    assert state.settings is original_dict
    assert state.settings["nested"] is original_nested


def test_dict_widget_adds_new_keys():
    state = ContainerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"settings": "dict"})
    widget.settings = {"visible": True, "nested": {"x": 1, "y": 2}, "new_key": "hello"}
    assert state.settings["new_key"] == "hello"


def test_dict_widget_removes_keys():
    state = ContainerState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"settings": "dict"})
    widget.settings = {"visible": True}
    assert "nested" not in state.settings


def test_list_plain_callback_property():
    """connect_list works with a regular CallbackProperty holding a plain list."""

    class PlainListState(HasCallbackProperties):
        open_panels = CallbackProperty([])

    state = PlainListState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"open_panels": "list"})

    assert widget.open_panels == []
    state.open_panels = [0, 2]
    assert widget.open_panels == [0, 2]
    # Widget→state does full replacement (not in-place) for plain lists
    widget.open_panels = [1, 3]
    assert state.open_panels == [1, 3]


def test_list_and_dict_via_extras():
    template = '<template><v-switch v-model="flag" /></template>'

    class MixedState(HasCallbackProperties):
        flag = CallbackProperty(True)
        items = ListCallbackProperty([1, 2, 3])
        config = DictCallbackProperty({"a": 1})

    state = MixedState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(
        state,
        widget,
        template=template,
        extras={"items": "list", "config": "dict"},
    )
    assert "flag" in handlers
    assert "items" in handlers
    assert "config" in handlers
    assert widget.items == [1, 2, 3]
    assert widget.config == {"a": 1}


# --- Auto-inferred type tests ---


def test_only_as_set_infers_types():
    """only as a set auto-infers types from property descriptors."""

    class AutoState(HasCallbackProperties):
        name = CallbackProperty("hello")
        visible = CallbackProperty(True)
        items = ListCallbackProperty([1, 2])
        config = DictCallbackProperty({"a": 1})
        choice = SelectionCallbackProperty(default_index=0)

    AutoState.choice.set_choices(AutoState, ["x", "y"])

    state = AutoState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(
        state,
        widget,
        only={"name", "visible", "items", "config", "choice"},
    )
    assert set(handlers) == {"name", "visible", "items", "config", "choice"}

    # Scalar properties use Any traitlet — bidirectional sync works
    assert widget.name == "hello"
    state.name = "world"
    assert widget.name == "world"
    widget.name = "back"
    assert state.name == "back"

    assert widget.visible is True
    state.visible = False
    assert widget.visible is False

    # List inferred from ListCallbackProperty
    assert widget.items == [1, 2]
    state.items.append(3)
    assert widget.items == [1, 2, 3]

    # Dict inferred from DictCallbackProperty
    assert widget.config == {"a": 1}
    state.config["b"] = 2
    assert widget.config == {"a": 1, "b": 2}

    # Selection inferred from SelectionCallbackProperty
    assert hasattr(widget, "choice_items")
    assert hasattr(widget, "choice_selected")


def test_any_handles_plain_list_value():
    """connect_any works for a CallbackProperty whose value is a plain list."""

    class PlainState(HasCallbackProperties):
        open_panels = CallbackProperty([])

    state = PlainState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(state, widget, only={"open_panels"})
    assert widget.open_panels == []
    state.open_panels = [0, 2]
    assert widget.open_panels == [0, 2]
    widget.open_panels = [1]
    assert state.open_panels == [1]


def test_infer_from_python_discovers_all():
    """infer_properties_from='python' discovers all callback properties."""

    class FullState(HasCallbackProperties):
        name = CallbackProperty("hi")
        items = ListCallbackProperty([1])
        config = DictCallbackProperty({"a": 1})
        _private = CallbackProperty("skip")  # should be skipped (starts with _)

    state = FullState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(state, widget, infer_properties_from="python")
    assert set(handlers) == {"name", "items", "config"}

    state.name = "bye"
    assert widget.name == "bye"
    state.items.append(2)
    assert widget.items == [1, 2]
    state.config["b"] = 2
    assert widget.config == {"a": 1, "b": 2}


def test_infer_from_python_with_skip():
    """infer_properties_from='python' respects the skip parameter."""

    class SkipState(HasCallbackProperties):
        a = CallbackProperty(1)
        b = CallbackProperty(2)
        c = CallbackProperty(3)

    state = SkipState()
    widget = SimpleWidget()
    handlers = autoconnect_callbacks_to_vue(state, widget, infer_properties_from="python", skip={"b"})
    assert "a" in handlers
    assert "b" not in handlers
    assert "c" in handlers


def test_infer_from_python_with_extras():
    """infer_properties_from='python' + extras for custom transforms."""

    class TransformState(HasCallbackProperties):
        name = CallbackProperty("hello")
        value = CallbackProperty(10)

    state = TransformState()
    widget = SimpleWidget()
    autoconnect_callbacks_to_vue(
        state,
        widget,
        infer_properties_from="python",
        extras={"value": ("text", str, int)},
    )
    # name auto-inferred as 'any', value overridden to 'text' with transforms
    assert widget.name == "hello"
    assert widget.value == "10"
    widget.value = "42"
    assert state.value == 42
