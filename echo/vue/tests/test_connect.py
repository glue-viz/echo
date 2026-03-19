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
        self.widget.add_traits(bool_flag=traitlets.Bool(False).tag(sync=True))
        self.conn = connect_bool(self.state, 'flag', self.widget, 'bool_flag')

    def test_state_to_widget(self):
        self.state.flag = True
        assert self.widget.bool_flag is True
        self.state.flag = False
        assert self.widget.bool_flag is False

    def test_widget_to_state(self):
        self.widget.bool_flag = True
        assert self.state.flag is True
        self.widget.bool_flag = False
        assert self.state.flag is False

    def test_initial_sync(self):
        assert self.widget.bool_flag == self.state.flag

    def test_disconnect(self):
        self.conn.disconnect()
        self.state.flag = True
        assert self.widget.bool_flag is False

    def test_auto_create_trait(self):
        state = SimpleState()
        widget = SimpleWidget()
        conn = connect_bool(state, 'flag', widget)
        assert hasattr(widget, 'bool_flag')
        state.flag = True
        assert widget.bool_flag is True
        conn.disconnect()


class TestConnectValue:

    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(value_height=traitlets.Float(allow_none=True).tag(sync=True))
        self.conn = connect_value(self.state, 'height', self.widget, 'value_height')

    def test_state_to_widget(self):
        self.state.height = 2.5
        assert self.widget.value_height == 2.5

    def test_widget_to_state(self):
        self.widget.value_height = 3.0
        assert self.state.height == 3.0

    def test_initial_sync(self):
        assert self.widget.value_height == 1.5

    def test_none_handling(self):
        self.state.height = None
        assert self.widget.value_height is None

    def test_auto_create_trait(self):
        state = SimpleState()
        widget = SimpleWidget()
        conn = connect_value(state, 'count', widget)
        assert hasattr(widget, 'value_count')
        state.count = 42
        assert widget.value_count == 42.0
        conn.disconnect()


class TestConnectValueText:

    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(valuetext_age=traitlets.Unicode('').tag(sync=True))
        self.conn = connect_valuetext(self.state, 'age', self.widget, 'valuetext_age')

    def test_state_to_widget(self):
        self.state.age = 30
        assert self.widget.valuetext_age == '30'

    def test_widget_to_state(self):
        self.widget.valuetext_age = '42'
        assert self.state.age == 42.0

    def test_invalid_input(self):
        self.state.age = 25
        self.widget.valuetext_age = 'not a number'
        assert self.state.age == 25  # unchanged


class TestConnectText:

    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(text_name=traitlets.Unicode('').tag(sync=True))
        self.conn = connect_text(self.state, 'name', self.widget, 'text_name')

    def test_state_to_widget(self):
        self.state.name = 'hello'
        assert self.widget.text_name == 'hello'

    def test_widget_to_state(self):
        self.widget.text_name = 'world'
        assert self.state.name == 'world'

    def test_initial_sync(self):
        assert self.widget.text_name == 'default'

    def test_none_handling(self):
        self.state.name = None
        assert self.widget.text_name == ''


class TestConnectChoice:

    def setup_method(self):
        self.state = SimpleState()
        self.widget = SimpleWidget()
        self.widget.add_traits(
            combosel_color_items=traitlets.List().tag(sync=True),
            combosel_color_selected=traitlets.Int(allow_none=True).tag(sync=True),
        )
        self.conn = connect_choice(
            self.state, 'color', self.widget, 'combosel_color_selected',
        )

    def test_items_populated(self):
        items = self.widget.combosel_color_items
        assert len(items) == 3
        assert items[0]['text'] == 'RED'
        assert items[1]['text'] == 'GREEN'
        assert items[2]['text'] == 'BLUE'

    def test_state_to_widget(self):
        self.state.color = 'blue'
        assert self.widget.combosel_color_selected == 2

    def test_widget_to_state(self):
        self.widget.combosel_color_selected = 1
        assert self.state.color == 'green'

    def test_initial_sync(self):
        assert self.widget.combosel_color_selected == 0
        assert self.state.color == 'red'

    def test_auto_create_traits(self):
        state = SimpleState()
        widget = SimpleWidget()
        conn = connect_choice(state, 'color', widget)
        assert hasattr(widget, 'combosel_color_items')
        assert hasattr(widget, 'combosel_color_selected')
        assert len(widget.combosel_color_items) == 3
        conn.disconnect()
