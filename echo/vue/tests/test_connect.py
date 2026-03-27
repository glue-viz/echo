import pytest

traitlets = pytest.importorskip("traitlets")

from echo import (  # noqa: E402  # noqa: E402
    CallbackProperty,
    DictCallbackProperty,
    HasCallbackProperties,
    ListCallbackProperty,
    SelectionCallbackProperty,
)
from echo.vue._connect import (  # noqa: E402
    connect_any,
    connect_bool,
    connect_choice,
    connect_dict,
    connect_float,
    connect_list,
    connect_text,
)


class SimpleState(HasCallbackProperties):
    flag = CallbackProperty(False)
    height = CallbackProperty(1.5)
    count = CallbackProperty(10)
    name = CallbackProperty("default")
    age = CallbackProperty(25)
    color = SelectionCallbackProperty(default_index=0)

    def __init__(self):
        super().__init__()
        SimpleState.color.set_choices(self, ["red", "green", "blue"])
        SimpleState.color.set_display_func(self, str.upper)


class SimpleWidget(traitlets.HasTraits):
    pass


class TestConnectBool:
    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(flag=traitlets.Bool(False).tag(sync=True))
        self.conn = connect_bool(self.state, "flag", self.widget, "flag")

    def test_state_to_widget(self):
        self.state.flag = True
        assert self.widget.flag is True
        self.state.flag = False
        assert self.widget.flag is False

    def test_widget_to_state(self):
        self.widget.flag = True
        assert self.state.flag is True
        self.widget.flag = False
        assert self.state.flag is False

    def test_initial_sync(self):
        assert self.widget.flag == self.state.flag

    def test_disconnect(self):
        self.conn.disconnect()
        self.state.flag = True
        assert self.widget.flag is False

    def test_auto_create_trait(self):
        state = SimpleState()
        widget = SimpleWidget()
        conn = connect_bool(state, "flag", widget)
        assert hasattr(widget, "flag")
        state.flag = True
        assert widget.flag is True
        conn.disconnect()


class TestConnectValue:
    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(height=traitlets.Float(allow_none=True).tag(sync=True))
        self.conn = connect_float(self.state, "height", self.widget, "height")

    def test_state_to_widget(self):
        self.state.height = 2.5
        assert self.widget.height == 2.5

    def test_widget_to_state(self):
        self.widget.height = 3.0
        assert self.state.height == 3.0

    def test_initial_sync(self):
        assert self.widget.height == 1.5

    def test_none_handling(self):
        self.state.height = None
        assert self.widget.height is None

    def test_auto_create_trait(self):
        state = SimpleState()
        widget = SimpleWidget()
        conn = connect_float(state, "count", widget)
        assert hasattr(widget, "count")
        state.count = 42
        assert widget.count == 42.0
        conn.disconnect()


class TestConnectText:
    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(name=traitlets.Unicode("").tag(sync=True))
        self.conn = connect_text(self.state, "name", self.widget, "name")

    def test_state_to_widget(self):
        self.state.name = "hello"
        assert self.widget.name == "hello"

    def test_widget_to_state(self):
        self.widget.name = "world"
        assert self.state.name == "world"

    def test_initial_sync(self):
        assert self.widget.name == "default"

    def test_none_handling(self):
        self.state.name = None
        assert self.widget.name == ""


class TestConnectChoice:
    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(
            color_items=traitlets.List().tag(sync=True),
            color_selected=traitlets.Int(allow_none=True).tag(sync=True),
        )
        self.conn = connect_choice(
            self.state,
            "color",
            self.widget,
            "color_selected",
        )

    def test_items_populated(self):
        items = self.widget.color_items
        assert len(items) == 3
        assert items[0]["text"] == "RED"
        assert items[1]["text"] == "GREEN"
        assert items[2]["text"] == "BLUE"

    def test_state_to_widget(self):
        self.state.color = "blue"
        assert self.widget.color_selected == 2

    def test_widget_to_state(self):
        self.widget.color_selected = 1
        assert self.state.color == "green"

    def test_initial_sync(self):
        assert self.widget.color_selected == 0
        assert self.state.color == "red"

    def test_auto_create_traits(self):
        state = SimpleState()
        widget = SimpleWidget()
        conn = connect_choice(state, "color", widget)
        assert hasattr(widget, "color_items")
        assert hasattr(widget, "color_selected")
        assert len(widget.color_items) == 3
        conn.disconnect()

    def test_current_not_in_choices(self):
        """When the current value isn't in choices, selected is set to None."""
        state = SimpleState()
        widget = SimpleWidget()
        conn = connect_choice(state, "color", widget)
        assert widget.color_selected == 0
        # Temporarily override _get_choices to return choices that don't
        # include the current value, then trigger a sync.
        orig = conn._get_choices
        conn._get_choices = lambda: (["cyan", "magenta"], ["cyan", "magenta"])
        conn._updating = False
        conn._from_state()
        assert widget.color_selected is None
        conn._get_choices = orig

    def test_widget_set_none(self):
        """Setting selected to None does not change the state."""
        state = SimpleState()
        widget = SimpleWidget()
        connect_choice(state, "color", widget)
        current = state.color
        widget.color_selected = None
        assert state.color == current

    def test_widget_set_out_of_range(self):
        """Setting selected to an out-of-range index does not change the state."""
        state = SimpleState()
        widget = SimpleWidget()
        connect_choice(state, "color", widget)
        current = state.color
        widget.color_selected = 99
        assert state.color == current


class ContainerState(HasCallbackProperties):
    items = ListCallbackProperty([{"name": "a"}, {"name": "b"}])
    config = DictCallbackProperty({"x": 1, "nested": {"y": 2}})
    tags = ListCallbackProperty(["red", "green"])
    plain_list = CallbackProperty([0, 1])


class TestConnectList:
    def setup_method(self):
        self.state = ContainerState()
        self.widget = SimpleWidget()
        self.conn = connect_list(self.state, "items", self.widget)

    def test_initial_sync(self):
        assert self.widget.items == [{"name": "a"}, {"name": "b"}]

    def test_state_to_widget(self):
        self.state.items.append({"name": "c"})
        assert len(self.widget.items) == 3
        assert self.widget.items[2] == {"name": "c"}

    def test_widget_to_state(self):
        self.widget.items = [{"name": "x"}]
        assert len(self.state.items) == 1
        assert self.state.items[0] == {"name": "x"}

    def test_in_place_update(self):
        original = self.state.items
        self.widget.items = [{"name": "x"}, {"name": "y"}]
        assert self.state.items is original

    def test_auto_create_trait(self):
        state = ContainerState()
        widget = SimpleWidget()
        connect_list(state, "tags", widget)
        assert hasattr(widget, "tags")
        assert widget.tags == ["red", "green"]

    def test_disconnect(self):
        self.conn.disconnect()
        self.state.items.append({"name": "c"})
        assert len(self.widget.items) == 2

    def test_plain_list_fallback(self):
        """CallbackProperty holding a plain list uses setattr instead of in-place."""
        state = ContainerState()
        widget = SimpleWidget()
        connect_list(state, "plain_list", widget)
        assert widget.plain_list == [0, 1]
        widget.plain_list = [3, 4]
        assert state.plain_list == [3, 4]


class TestConnectDict:
    def setup_method(self):
        self.state = ContainerState()
        self.widget = SimpleWidget()
        self.conn = connect_dict(self.state, "config", self.widget)

    def test_initial_sync(self):
        assert self.widget.config == {"x": 1, "nested": {"y": 2}}

    def test_state_to_widget(self):
        self.state.config["x"] = 99
        assert self.widget.config["x"] == 99

    def test_nested_mutation(self):
        self.state.config["nested"]["y"] = 42
        assert self.widget.config["nested"]["y"] == 42

    def test_widget_to_state(self):
        self.widget.config = {"x": 5, "nested": {"y": 6}}
        assert self.state.config["x"] == 5
        assert self.state.config["nested"]["y"] == 6

    def test_in_place_update(self):
        original = self.state.config
        original_nested = self.state.config["nested"]
        self.widget.config = {"x": 5, "nested": {"y": 6}}
        assert self.state.config is original
        assert self.state.config["nested"] is original_nested

    def test_auto_create_trait(self):
        state = ContainerState()
        widget = SimpleWidget()
        connect_dict(state, "config", widget)
        assert hasattr(widget, "config")

    def test_disconnect(self):
        self.conn.disconnect()
        self.state.config["x"] = 99
        assert self.widget.config["x"] == 1


class TestConnectAny:
    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.conn = connect_any(self.state, "name", self.widget)

    def test_initial_sync(self):
        assert self.widget.name == "default"

    def test_state_to_widget(self):
        self.state.name = "hello"
        assert self.widget.name == "hello"

    def test_widget_to_state(self):
        self.widget.name = "world"
        assert self.state.name == "world"

    def test_auto_create_trait(self):
        state = SimpleState()
        widget = SimpleWidget()
        connect_any(state, "height", widget)
        assert hasattr(widget, "height")
        assert widget.height == 1.5

    def test_disconnect(self):
        self.conn.disconnect()
        self.state.name = "changed"
        assert self.widget.name == "default"

    def test_no_type_coercion(self):
        """connect_any passes values through without coercion."""
        state = SimpleState()
        widget = SimpleWidget()
        connect_any(state, "flag", widget)
        state.flag = True
        assert widget.flag is True
        state.flag = 0
        assert widget.flag == 0  # not coerced to bool


@pytest.mark.parametrize(
    "connect_cls, prop, initial, new_state, new_widget",
    [
        (connect_bool, "flag", False, True, False),
        (connect_float, "height", 1.5, 3.0, 7.0),
        (connect_text, "name", "default", "hello", "world"),
    ],
)
def test_transforms(connect_cls, prop, initial, new_state, new_widget):
    """to_widget and from_widget transforms are applied."""
    state = SimpleState()
    widget = SimpleWidget()
    conn = connect_cls(state, prop, widget, to_widget=lambda v: v, from_widget=lambda v: v)
    assert getattr(widget, prop) == initial
    setattr(state, prop, new_state)
    assert getattr(widget, prop) == new_state
    setattr(widget, prop, new_widget)
    assert getattr(state, prop) == new_widget
    conn.disconnect()
