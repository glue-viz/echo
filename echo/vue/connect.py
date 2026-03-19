# The classes in this module are used to connect callback properties to
# ipywidgets/ipyvuetify traitlets. Each connection is atomic per-property:
# changing a property on the widget only syncs that single property to the
# state, avoiding stale-overwrite issues that arise from syncing the entire
# state dict at once.

import traitlets

from ..core import add_callback, remove_callback
from ..selection import ChoiceSeparator

__all__ = ['connect_bool', 'connect_value', 'connect_valuetext',
           'connect_text', 'connect_choice', 'BaseConnection']


class BaseConnection:
    """
    Base class for bidirectional connections between a callback property
    and an ipywidgets/ipyvuetify traitlet.

    Parameters
    ----------
    instance : object
        The class instance that the callback property is attached to.
    prop : str
        The name of the callback property.
    widget : HasTraits
        The ipywidgets/ipyvuetify widget.
    widget_prop : str
        The name of the traitlet on the widget.
    """

    def __init__(self, instance, prop, widget, widget_prop):
        self._instance = instance
        self._prop = prop
        self._widget = widget
        self._widget_prop = widget_prop
        self._updating = False

    def _from_state(self, *args):
        if self._updating:
            return
        self._updating = True
        try:
            value = getattr(self._instance, self._prop)
            self.update_widget(value)
        finally:
            self._updating = False

    def _from_widget(self, change):
        if self._updating:
            return
        self._updating = True
        try:
            self.update_prop(change['new'])
        finally:
            self._updating = False

    def connect(self):
        add_callback(self._instance, self._prop, self._from_state)
        self._widget.observe(self._from_widget, names=[self._widget_prop])
        self._from_state()

    def disconnect(self):
        remove_callback(self._instance, self._prop, self._from_state)
        self._widget.unobserve(self._from_widget, names=[self._widget_prop])


class connect_bool(BaseConnection):
    """
    Connect a boolean callback property to a Bool traitlet.

    Parameters
    ----------
    instance : object
        The class instance that the callback property is attached to.
    prop : str
        The name of the callback property.
    widget : HasTraits
        The widget. If ``widget_prop`` is not given, a traitlet named
        ``bool_{prop}`` is created dynamically.
    widget_prop : str, optional
        The name of the Bool traitlet on the widget.
    """

    def __init__(self, instance, prop, widget, widget_prop=None):
        if widget_prop is None:
            widget_prop = f'bool_{prop}'
        if not widget.has_trait(widget_prop):
            widget.add_traits(**{widget_prop: traitlets.Bool(False).tag(sync=True)})
        super().__init__(instance, prop, widget, widget_prop)
        self.connect()

    def update_widget(self, value):
        setattr(self._widget, self._widget_prop, bool(value) if value is not None else False)

    def update_prop(self, value):
        setattr(self._instance, self._prop, value)


class connect_value(BaseConnection):
    """
    Connect a numeric callback property to a Float traitlet.

    Parameters
    ----------
    instance : object
        The class instance that the callback property is attached to.
    prop : str
        The name of the callback property.
    widget : HasTraits
        The widget. If ``widget_prop`` is not given, a traitlet named
        ``value_{prop}`` is created dynamically.
    widget_prop : str, optional
        The name of the Float traitlet on the widget.
    """

    def __init__(self, instance, prop, widget, widget_prop=None):
        if widget_prop is None:
            widget_prop = f'value_{prop}'
        if not widget.has_trait(widget_prop):
            widget.add_traits(**{widget_prop: traitlets.Float(allow_none=True).tag(sync=True)})
        super().__init__(instance, prop, widget, widget_prop)
        self.connect()

    def update_widget(self, value):
        setattr(self._widget, self._widget_prop, float(value) if value is not None else None)

    def update_prop(self, value):
        setattr(self._instance, self._prop, value)


class connect_valuetext(BaseConnection):
    """
    Connect a numeric callback property to a Unicode traitlet (displayed as text).

    Parameters
    ----------
    instance : object
        The class instance that the callback property is attached to.
    prop : str
        The name of the callback property.
    widget : HasTraits
        The widget. If ``widget_prop`` is not given, a traitlet named
        ``valuetext_{prop}`` is created dynamically.
    widget_prop : str, optional
        The name of the Unicode traitlet on the widget.
    """

    def __init__(self, instance, prop, widget, widget_prop=None):
        if widget_prop is None:
            widget_prop = f'valuetext_{prop}'
        if not widget.has_trait(widget_prop):
            widget.add_traits(**{widget_prop: traitlets.Unicode('').tag(sync=True)})
        super().__init__(instance, prop, widget, widget_prop)
        self.connect()

    def update_widget(self, value):
        setattr(self._widget, self._widget_prop, str(value) if value is not None else '')

    def update_prop(self, value):
        try:
            setattr(self._instance, self._prop, float(value))
        except (ValueError, TypeError):
            pass


class connect_text(BaseConnection):
    """
    Connect a string callback property to a Unicode traitlet.

    Parameters
    ----------
    instance : object
        The class instance that the callback property is attached to.
    prop : str
        The name of the callback property.
    widget : HasTraits
        The widget. If ``widget_prop`` is not given, a traitlet named
        ``text_{prop}`` is created dynamically.
    widget_prop : str, optional
        The name of the Unicode traitlet on the widget.
    """

    def __init__(self, instance, prop, widget, widget_prop=None):
        if widget_prop is None:
            widget_prop = f'text_{prop}'
        if not widget.has_trait(widget_prop):
            widget.add_traits(**{widget_prop: traitlets.Unicode('').tag(sync=True)})
        super().__init__(instance, prop, widget, widget_prop)
        self.connect()

    def update_widget(self, value):
        setattr(self._widget, self._widget_prop, str(value) if value is not None else '')

    def update_prop(self, value):
        setattr(self._instance, self._prop, value)


class connect_choice(BaseConnection):
    """
    Connect a SelectionCallbackProperty to a pair of traitlets:
    ``combosel_{prop}_items`` (List) and ``combosel_{prop}_selected`` (Int).

    Parameters
    ----------
    instance : object
        The class instance that the callback property is attached to.
    prop : str
        The name of the SelectionCallbackProperty.
    widget : HasTraits
        The widget. If ``widget_prop`` is not given, traitlets named
        ``combosel_{prop}_items`` and ``combosel_{prop}_selected`` are
        created dynamically.
    widget_prop : str, optional
        The name of the Int (selected) traitlet. The items traitlet is
        derived by replacing ``_selected`` with ``_items``.
    """

    def __init__(self, instance, prop, widget, widget_prop=None):
        if widget_prop is None:
            widget_prop = f'combosel_{prop}_selected'
        items_prop = widget_prop.replace('_selected', '_items')
        traits = {}
        if not widget.has_trait(widget_prop):
            traits[widget_prop] = traitlets.Int(allow_none=True).tag(sync=True)
        if not widget.has_trait(items_prop):
            traits[items_prop] = traitlets.List().tag(sync=True)
        if traits:
            widget.add_traits(**traits)
        self._items_prop = items_prop
        super().__init__(instance, prop, widget, widget_prop)
        self.connect()

    def _get_choices(self):
        prop_descriptor = getattr(type(self._instance), self._prop)
        display_func = prop_descriptor.get_display_func(self._instance) or str
        choices = []
        labels = []
        for choice in prop_descriptor.get_choices(self._instance):
            if not isinstance(choice, ChoiceSeparator):
                choices.append(choice)
                labels.append(display_func(choice))
        return choices, labels

    def _from_state(self, *args):
        if self._updating:
            return
        self._updating = True
        try:
            choices, labels = self._get_choices()
            items = [{'text': label, 'value': i} for i, label in enumerate(labels)]
            setattr(self._widget, self._items_prop, items)
            current = getattr(self._instance, self._prop)
            if current in choices:
                setattr(self._widget, self._widget_prop, choices.index(current))
            else:
                setattr(self._widget, self._widget_prop, None)
        finally:
            self._updating = False

    def update_widget(self, value):
        pass  # Handled by _from_state

    def update_prop(self, index):
        if index is None:
            return
        choices, _ = self._get_choices()
        if 0 <= index < len(choices):
            setattr(self._instance, self._prop, choices[index])
