# The classes in this module are used to connect callback properties to
# ipywidgets/ipyvuetify traitlets. Each connection is atomic per-property:
# changing a property on the widget only syncs that single property to the
# state, avoiding stale-overwrite issues that arise from syncing the entire
# state dict at once.

import traitlets

from ..core import add_callback, remove_callback
from ..selection import ChoiceSeparator

__all__ = ['connect_bool', 'connect_int', 'connect_float',
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
    widget_prop : str, optional
        The name of the traitlet on the widget. Defaults to ``prop``.
    to_widget : callable, optional
        Transform applied when syncing state -> widget. Receives the raw
        property value and returns the value to set on the traitlet.
        Overrides the subclass default conversion.
    from_widget : callable, optional
        Transform applied when syncing widget -> state. Receives the
        traitlet value and returns the value to set on the property.
        Overrides the subclass default conversion.
    """

    # Subclasses set this to a callable returning a traitlet instance,
    # used when the widget does not already have a matching trait.
    _default_trait = None

    def __init__(self, instance, prop, widget, widget_prop=None,
                 to_widget=None, from_widget=None, initial_sync=True):
        if widget_prop is None:
            widget_prop = prop
        if self._default_trait and not widget.has_trait(widget_prop):
            trait = self._default_trait()
            if not initial_sync:
                # Create without sync tag so add_traits doesn't send state.
                # The caller is responsible for enabling sync later via
                # enable_widget_sync().
                trait.metadata.pop('sync', None)
            widget.add_traits(**{widget_prop: trait})
        self._instance = instance
        self._prop = prop
        self._widget = widget
        self._widget_prop = widget_prop
        self._to_widget_transform = to_widget
        self._from_widget_transform = from_widget
        self._updating = False
        self.connect(initial_sync=initial_sync)

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

    def update_prop(self, value):
        if self._from_widget_transform is not None:
            value = self._from_widget_transform(value)
        setattr(self._instance, self._prop, value)

    def connect(self, initial_sync=True):
        add_callback(self._instance, self._prop, self._from_state)
        self._widget.observe(self._from_widget, names=[self._widget_prop])
        if initial_sync:
            self._from_state()

    def enable_widget_sync(self):
        """Tag the widget trait(s) as sync=True and register in widget.keys."""
        for name in self._sync_trait_names():
            trait = self._widget.traits()[name]
            if 'sync' not in trait.metadata:
                trait.tag(sync=True)
                if hasattr(self._widget, 'keys'):
                    self._widget.keys.append(name)

    def _sync_trait_names(self):
        return [self._widget_prop]

    def disconnect(self):
        remove_callback(self._instance, self._prop, self._from_state)
        self._widget.unobserve(self._from_widget, names=[self._widget_prop])


class connect_bool(BaseConnection):
    """Connect a boolean callback property to a Bool traitlet."""

    _default_trait = staticmethod(lambda: traitlets.Bool(False).tag(sync=True))

    def update_widget(self, value):
        if self._to_widget_transform is not None:
            value = self._to_widget_transform(value)
        else:
            value = bool(value) if value is not None else False
        setattr(self._widget, self._widget_prop, value)


class connect_int(BaseConnection):
    """Connect an integer callback property to an Int traitlet."""

    _default_trait = staticmethod(
        lambda: traitlets.CInt(0).tag(sync=True))

    def update_widget(self, value):
        if self._to_widget_transform is not None:
            value = self._to_widget_transform(value)
        else:
            value = int(value) if value is not None else 0
        setattr(self._widget, self._widget_prop, value)


class connect_float(BaseConnection):
    """Connect a numeric callback property to a Float traitlet."""

    _default_trait = staticmethod(
        lambda: traitlets.Float(allow_none=True).tag(sync=True))

    def update_widget(self, value):
        if self._to_widget_transform is not None:
            value = self._to_widget_transform(value)
        else:
            value = float(value) if value is not None else None
        setattr(self._widget, self._widget_prop, value)


class connect_text(BaseConnection):
    """Connect a string callback property to a Unicode traitlet."""

    _default_trait = staticmethod(
        lambda: traitlets.Unicode('').tag(sync=True))

    def update_widget(self, value):
        if self._to_widget_transform is not None:
            value = self._to_widget_transform(value)
        else:
            value = str(value) if value is not None else ''
        setattr(self._widget, self._widget_prop, value)


class connect_choice(BaseConnection):
    """
    Connect a SelectionCallbackProperty to a pair of traitlets:
    ``{prop}_items`` (List) and ``{prop}_selected`` (Int).
    """

    def __init__(self, instance, prop, widget, widget_prop=None, **kwargs):
        if widget_prop is None:
            widget_prop = f'{prop}_selected'
        items_prop = widget_prop.replace('_selected', '_items')
        initial_sync = kwargs.get('initial_sync', True)
        traits = {}
        if not widget.has_trait(widget_prop):
            trait = traitlets.Int(allow_none=True)
            if initial_sync:
                trait.tag(sync=True)
            traits[widget_prop] = trait
        if not widget.has_trait(items_prop):
            trait = traitlets.List()
            if initial_sync:
                trait.tag(sync=True)
            traits[items_prop] = trait
        if traits:
            widget.add_traits(**traits)
        self._items_prop = items_prop
        super().__init__(instance, prop, widget, widget_prop, **kwargs)

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

    def _sync_trait_names(self):
        return [self._widget_prop, self._items_prop]

    def update_widget(self, value):  # pragma: no cover
        pass  # Handled by _from_state

    def update_prop(self, index):
        if index is None:
            return
        choices, _ = self._get_choices()
        if 0 <= index < len(choices):
            setattr(self._instance, self._prop, choices[index])
