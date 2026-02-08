import pytest
import warnings
from unittest.mock import MagicMock

from echo import (CallbackProperty, CallbackPropertyAlias,
                  add_callback, remove_callback, delay_callback,
                  ignore_callback, HasCallbackProperties)
from echo.selection import SelectionCallbackProperty


class SimpleClass:
    """Simple class with a callback property and a silent alias."""
    color = CallbackProperty('red')
    colour = CallbackPropertyAlias('color')


class SimpleClassDeprecated:
    """Simple class with a deprecated alias (emits warning)."""
    color = CallbackProperty('red')
    colour = CallbackPropertyAlias('color', deprecated=True)


class SimpleClassCustomWarning:
    """Simple class with a custom deprecation warning."""
    color = CallbackProperty('red')
    colour = CallbackPropertyAlias('color', warning='Use color instead of colour!')


class SelectionClass:
    """Class with a SelectionCallbackProperty and an alias."""
    color = SelectionCallbackProperty(default='red', choices=['red', 'green', 'blue'])
    colour = CallbackPropertyAlias('color')


class HasCallbackPropertiesClass(HasCallbackProperties):
    """Class using HasCallbackProperties mixin with an alias."""
    color = CallbackProperty('red')
    colour = CallbackPropertyAlias('color')
    size = CallbackProperty(10)


# ============== Basic get/set tests ==============

def test_alias_get():
    """Test that getting via alias returns the target property value."""
    obj = SimpleClass()
    assert obj.colour == 'red'


def test_alias_set():
    """Test that setting via alias sets the target property value."""
    obj = SimpleClass()
    obj.colour = 'blue'
    assert obj.color == 'blue'


def test_alias_get_set_roundtrip():
    """Test get/set roundtrip through alias."""
    obj = SimpleClass()
    obj.colour = 'green'
    assert obj.colour == 'green'
    assert obj.color == 'green'


# ============== Deprecation warning tests ==============

def test_alias_no_deprecation_warning_by_default():
    """Test that no warning is emitted by default (deprecated=False)."""
    obj = SimpleClass()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        # Should not raise any warnings
        obj.colour = 'blue'
        _ = obj.colour


def test_alias_emits_deprecation_warning_on_get():
    """Test that deprecation warning is emitted on get when deprecated=True."""
    obj = SimpleClassDeprecated()
    with pytest.warns(DeprecationWarning, match="'colour' is deprecated, use 'color' instead"):
        _ = obj.colour


def test_alias_emits_deprecation_warning_on_set():
    """Test that deprecation warning is emitted on set when deprecated=True."""
    obj = SimpleClassDeprecated()
    with pytest.warns(DeprecationWarning, match="'colour' is deprecated, use 'color' instead"):
        obj.colour = 'blue'


def test_alias_custom_warning_message():
    """Test that custom warning message is used."""
    obj = SimpleClassCustomWarning()
    with pytest.warns(DeprecationWarning, match='Use color instead of colour!'):
        _ = obj.colour


# ============== Callback tests ==============

def test_add_callback_via_alias():
    """Test that callbacks added via alias are attached to target property."""
    obj = SimpleClass()
    callback = MagicMock()

    add_callback(obj, 'colour', callback)

    # Changing via the real property should trigger callback
    obj.color = 'blue'
    callback.assert_called_once_with('blue')


def test_add_callback_via_deprecated_alias():
    """Test that callbacks added via deprecated alias emit warning."""
    obj = SimpleClassDeprecated()
    callback = MagicMock()

    with pytest.warns(DeprecationWarning):
        add_callback(obj, 'colour', callback)

    obj.color = 'blue'
    callback.assert_called_once_with('blue')


def test_remove_callback_via_alias():
    """Test that callbacks can be removed via alias."""
    obj = SimpleClass()
    callback = MagicMock()

    add_callback(obj, 'color', callback)
    remove_callback(obj, 'colour', callback)

    obj.color = 'blue'
    assert callback.call_count == 0


def test_callback_triggered_when_setting_via_alias():
    """Test that callbacks trigger when value is set via alias."""
    obj = SimpleClass()
    callback = MagicMock()

    add_callback(obj, 'color', callback)
    obj.colour = 'blue'

    callback.assert_called_once_with('blue')


def test_delay_callback_via_alias():
    """Test delay_callback works with alias property name."""
    obj = SimpleClass()
    callback = MagicMock()

    add_callback(obj, 'color', callback)

    with delay_callback(obj, 'colour'):
        obj.color = 'blue'
        obj.color = 'green'
        assert callback.call_count == 0

    callback.assert_called_once_with('green')


def test_ignore_callback_via_alias():
    """Test ignore_callback works with alias property name."""
    obj = SimpleClass()
    callback = MagicMock()

    add_callback(obj, 'color', callback)

    with ignore_callback(obj, 'colour'):
        obj.color = 'blue'
        assert callback.call_count == 0

    assert callback.call_count == 0


# ============== SelectionCallbackProperty tests ==============

def test_selection_alias_get_set():
    """Test that alias works with SelectionCallbackProperty."""
    obj = SelectionClass()

    assert obj.colour == 'red'
    obj.colour = 'blue'
    assert obj.color == 'blue'


def test_selection_alias_validation():
    """Test that validation still works when setting via alias."""
    obj = SelectionClass()

    with pytest.raises(ValueError, match='not in valid choices'):
        obj.colour = 'yellow'


def test_selection_alias_get_choices():
    """Test that get_choices can be accessed via alias."""
    obj = SelectionClass()

    # Access choices via class attribute proxy
    assert SelectionClass.colour.get_choices(obj) == ['red', 'green', 'blue']


def test_selection_alias_set_choices():
    """Test that set_choices can be accessed via alias."""
    obj = SelectionClass()

    # Set choices via class attribute proxy
    SelectionClass.colour.set_choices(obj, ['cyan', 'magenta', 'yellow'])

    assert obj.color == 'cyan'
    assert SelectionClass.color.get_choices(obj) == ['cyan', 'magenta', 'yellow']


def test_selection_alias_default_choices():
    """Test that default_choices attribute is proxied."""
    assert SelectionClass.colour.default_choices == ['red', 'green', 'blue']


# ============== HasCallbackProperties tests ==============

def test_has_callback_properties_is_callback_property():
    """Test that is_callback_property returns True for properties and aliases."""
    obj = HasCallbackPropertiesClass()
    assert obj.is_callback_property('color')
    assert obj.is_callback_property('colour')  # Alias also returns True
    assert obj.is_callback_property('size')


def test_has_callback_properties_is_alias():
    """Test that is_alias returns True only for aliases."""
    obj = HasCallbackPropertiesClass()
    assert not obj.is_alias('color')
    assert obj.is_alias('colour')
    assert not obj.is_alias('size')


def test_has_callback_properties_iter_excludes_aliases():
    """Test that iter_callback_properties does not include aliases."""
    obj = HasCallbackPropertiesClass()
    prop_names = [name for name, _ in obj.iter_callback_properties()]
    assert 'color' in prop_names
    assert 'size' in prop_names
    assert 'colour' not in prop_names


def test_has_callback_properties_callback_properties_excludes_aliases():
    """Test that callback_properties() does not include aliases."""
    obj = HasCallbackPropertiesClass()
    prop_names = obj.callback_properties()
    assert 'color' in prop_names
    assert 'size' in prop_names
    assert 'colour' not in prop_names


def test_has_callback_properties_add_callback_via_alias():
    """Test add_callback method on class with alias."""
    obj = HasCallbackPropertiesClass()
    callback = MagicMock()

    obj.add_callback('colour', callback)

    obj.color = 'blue'
    callback.assert_called_once_with('blue')


def test_has_callback_properties_remove_callback_via_alias():
    """Test remove_callback method on class with alias."""
    obj = HasCallbackPropertiesClass()
    callback = MagicMock()

    obj.add_callback('color', callback)
    obj.remove_callback('colour', callback)

    obj.color = 'blue'
    assert callback.call_count == 0


def test_has_callback_properties_global_callback_via_alias():
    """Test that global callbacks work when setting via alias."""
    obj = HasCallbackPropertiesClass()
    callback = MagicMock()

    obj.add_global_callback(callback)
    obj.colour = 'blue'

    callback.assert_called_once_with(color='blue')


# ============== Class attribute access tests ==============

def test_class_attribute_access_returns_alias():
    """Test that accessing alias on class returns the alias object."""
    assert isinstance(SimpleClass.colour, CallbackPropertyAlias)


def test_alias_target_property():
    """Test _target_property returns the correct CallbackProperty."""
    assert SimpleClass.colour._target_property is SimpleClass.color


def test_alias_getattr_proxy():
    """Test that __getattr__ proxies public attributes to target property."""
    # Test proxy by accessing methods on the target property
    # For SelectionCallbackProperty, get_choices is a method we can access
    obj = SelectionClass()
    # Accessing via alias should proxy to the target property's method
    choices = SelectionClass.colour.get_choices(obj)
    assert choices == ['red', 'green', 'blue']


# ============== Edge case tests ==============

def test_multiple_instances_independent():
    """Test that alias works correctly with multiple instances."""
    obj1 = SimpleClass()
    obj2 = SimpleClass()

    obj1.colour = 'blue'

    assert obj1.color == 'blue'
    assert obj2.color == 'red'


def test_alias_with_echo_old():
    """Test callback with echo_old via alias."""
    obj = SimpleClass()
    callback = MagicMock()

    obj.color = 'initial'
    add_callback(obj, 'colour', callback, echo_old=True)

    obj.color = 'new'
    callback.assert_called_once_with('initial', 'new')


def test_alias_with_validator():
    """Test validator callback via alias."""
    obj = SimpleClass()

    def uppercase_validator(value):
        return value.upper()

    add_callback(obj, 'colour', uppercase_validator, validator=True)

    obj.color = 'blue'
    assert obj.color == 'BLUE'
