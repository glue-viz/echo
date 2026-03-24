import pytest

traitlets = pytest.importorskip("traitlets")

from echo import CallbackProperty, SelectionCallbackProperty, HasCallbackProperties  # noqa: E402
from echo.vue.connect import (connect_bool, connect_value,  # noqa: E402
                              connect_valuetext, connect_text,
                              connect_choice)


class SimpleState(HasCallbackProperties):
    flag = CallbackProperty(False)
    height = CallbackProperty(1.5)
    count = CallbackProperty(10)
    name = CallbackProperty('default')
    age = CallbackProperty(25)
    color = SelectionCallbackProperty(default_index=0)

    def __init__(self):
        super().__init__()
        SimpleState.color.set_choices(self, ['red', 'green', 'blue'])
        SimpleState.color.set_display_func(self, str.upper)


class SimpleWidget(traitlets.HasTraits):
    pass


class TestConnectBool:

    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(flag=traitlets.Bool(False).tag(sync=True))
        self.conn = connect_bool(self.state, 'flag', self.widget, 'flag')

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
        conn = connect_bool(state, 'flag', widget)
        assert hasattr(widget, 'flag')
        state.flag = True
        assert widget.flag is True
        conn.disconnect()


class TestConnectValue:

    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(height=traitlets.Float(allow_none=True).tag(sync=True))
        self.conn = connect_value(self.state, 'height', self.widget, 'height')

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
        conn = connect_value(state, 'count', widget)
        assert hasattr(widget, 'count')
        state.count = 42
        assert widget.count == 42.0
        conn.disconnect()


class TestConnectValueText:

    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(age=traitlets.Unicode('').tag(sync=True))
        self.conn = connect_valuetext(self.state, 'age', self.widget, 'age')

    def test_state_to_widget(self):
        self.state.age = 30
        assert self.widget.age == '30'

    def test_widget_to_state(self):
        self.widget.age = '42'
        assert self.state.age == 42.0

    def test_invalid_input(self):
        self.state.age = 25
        self.widget.age = 'not a number'
        assert self.state.age == 25  # unchanged


class TestConnectText:

    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(name=traitlets.Unicode('').tag(sync=True))
        self.conn = connect_text(self.state, 'name', self.widget, 'name')

    def test_state_to_widget(self):
        self.state.name = 'hello'
        assert self.widget.name == 'hello'

    def test_widget_to_state(self):
        self.widget.name = 'world'
        assert self.state.name == 'world'

    def test_initial_sync(self):
        assert self.widget.name == 'default'

    def test_none_handling(self):
        self.state.name = None
        assert self.widget.name == ''


class TestConnectChoice:

    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(
            color_items=traitlets.List().tag(sync=True),
            color_selected=traitlets.Int(allow_none=True).tag(sync=True),
        )
        self.conn = connect_choice(
            self.state, 'color', self.widget, 'color_selected',
        )

    def test_items_populated(self):
        items = self.widget.color_items
        assert len(items) == 3
        assert items[0]['text'] == 'RED'
        assert items[1]['text'] == 'GREEN'
        assert items[2]['text'] == 'BLUE'

    def test_state_to_widget(self):
        self.state.color = 'blue'
        assert self.widget.color_selected == 2

    def test_widget_to_state(self):
        self.widget.color_selected = 1
        assert self.state.color == 'green'

    def test_initial_sync(self):
        assert self.widget.color_selected == 0
        assert self.state.color == 'red'

    def test_auto_create_traits(self):
        state = SimpleState()
        widget = SimpleWidget()
        conn = connect_choice(state, 'color', widget)
        assert hasattr(widget, 'color_items')
        assert hasattr(widget, 'color_selected')
        assert len(widget.color_items) == 3
        conn.disconnect()
